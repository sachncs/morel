"""End-to-end Pipeline: retrieve -> encode -> route -> codebook -> complete -> recommend.

Composes the five stages of the GRE-MC method into a single nn.Module so that
training and inference have one canonical entry point.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import cast

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn

from morel.codebook import build as build_codebook
from morel.complete import build as build_complete
from morel.core.config import Config
from morel.core.errors import Cfg, Model, Net
from morel.core.seed import deterministic
from morel.encode import build as build_encode
from morel.graph import Laplace
from morel.recommend import KIND as RECOMMEND_KIND
from morel.recommend import FeatureAware, Fits, Normalizes
from morel.recommend import build as build_recommend
from morel.retrieve import Result, batch
from morel.route import build as build_route


@dataclass
class Output:
    """Pipeline forward output.

    Attributes:
        completed: Per-modality completed features.
        routing: Routing probabilities.
        subgraph_indices: Subgraph node indices (optional).
        subgraph_mask: Subgraph mask (optional).
    """

    completed: dict[str, torch.Tensor]
    routing: torch.Tensor
    subgraph_indices: np.ndarray | None = None
    subgraph_mask: np.ndarray | None = None


@contextmanager
def mode(module: nn.Module, training: bool) -> Iterator[None]:
    """Run a block with ``module`` in the given train/eval mode, then restore.

    ``nn.Dropout`` and friends key off :attr:`torch.nn.Module.training`, which
    a ``training=`` keyword argument on a ``forward`` method does not change.
    Without this, asking a pipeline for an inference pass still applies
    dropout, which makes the result both wrong and nondeterministic.

    Args:
        module: Module whose mode (and that of its children) is switched.
        training: ``True`` for train mode, ``False`` for eval mode.

    Yields:
        ``None``. The block body runs with the requested mode applied.
    """
    previous = module.training
    module.train(training)
    try:
        yield
    finally:
        module.train(previous)


class Pipeline(nn.Module):
    """End-to-end GRE-MC pipeline.

    Attributes:
        encode: Joint encoder module.
        route: Router module.
        codebook: Codebook module.
        complete: Completion module.
        recommend: Recommender module.
    """

    def __init__(
        self,
        config: Config,
        *,
        dims: dict[str, int] | None = None,
    ) -> None:
        """Compose the GRE-MC stages into one module.

        Every parameter-bearing stage is initialized under ``config.seed``, so
        two pipelines built from the same config hold identical weights
        regardless of what the calling process did to the global RNG
        beforehand. The caller's RNG state is restored on exit.

        Each stage is selected by its ``kind`` in the configuration and built
        through the corresponding registry, so an implementation registered
        from outside this package is usable without touching this file.

        Args:
            config: Validated configuration supplying every stage's
                hyperparameters, implementation choice, and the
                initialization seed.
            dims: Per-modality input widths; defaults to the demo dims.

        Raises:
            Cfg: If any stage names an implementation that is not
                registered. The message lists the available names.
        """
        super().__init__()
        self.config = config
        if dims is None:
            dims = {"visual": 16, "text": 8}
        self.dims = dims
        self.encoder = Laplace(k=config.encode.pe)
        with deterministic(config.seed):
            self.transformer = build_encode(
                config.encode.kind,
                dims=dims,
                pe_dim=config.encode.pe,
                hidden=config.encode.hidden,
                layers=config.encode.layers,
                heads=config.encode.heads,
                dropout=config.encode.dropout,
            )
            self.router = build_route(
                config.route.kind,
                dim=config.encode.hidden,
                k=config.codebook.size,
                p=min(config.route.p, config.codebook.size),
                tau=config.route.tau,
            )
            self.codebook = build_codebook(
                config.codebook.kind,
                dim=config.encode.hidden,
                size=config.codebook.size,
                router=self.router,
                seed=config.seed,
            )
            self.decoders = build_complete(
                config.complete.kind,
                latent_dim=config.encode.hidden,
                dims=dims,
                hidden=config.complete.hidden,
            )
            # Validate the recommend kind eagerly so a bad config fails
            # at Pipeline construction, matching the other components.
            if config.recommend.kind not in RECOMMEND_KIND:
                raise Cfg(
                    f"unknown recommender '{config.recommend.kind}'; "
                    f"available: {', '.join(sorted(RECOMMEND_KIND))}"
                )
        self.recommender: nn.Module | None = None
        self.ui_graph: sp.csr_matrix | None = None
        self.cfeat: dict[str, np.ndarray] | None = None
        self.cmask: np.ndarray | None = None
        self.cadj: sp.csr_matrix | None = None
        self._score_cache: tuple[torch.device, torch.Tensor] | None = None
        self._retrieval_max_nodes: int | None = None

    def _invalidate_score_cache(self) -> None:
        """Drop completed catalog features cached by the serving score path."""
        self._score_cache = None

    def set_retrieval_budget(self, max_nodes: int | None) -> None:
        """Set an optional serving budget for retrieved subgraph size.

        A bounded serving budget prevents a large or adversarial catalog graph
        from turning one request into unbounded CPU or memory work. ``None``
        retains the research/training behavior without a serving cap.

        Args:
            max_nodes: Positive maximum node count, or ``None`` to disable.

        Raises:
        ValueError: If ``max_nodes`` is not positive when provided.
        """
        if max_nodes is not None and (isinstance(max_nodes, bool) or max_nodes <= 0):
            raise ValueError("max_nodes must be positive or None")
        self._retrieval_max_nodes = max_nodes

    @torch.no_grad()
    def warmup(self) -> None:
        """Materialize serving-time graph state before accepting requests.

        The graph positional encoding can be expensive for a large catalog.
        Serving callers should invoke this during startup so the first live
        request does not pay an unbounded graph-eigensolver cost.

        Raises:
        Model: If no item graph has been attached.
        """
        if self.cadj is None:
            raise Model("pipeline has no attached item graph to warm up")
        self.encoder(self.cadj)

    def train(self, mode: bool = True) -> Pipeline:
        """Switch train/eval mode and invalidate inference features for training."""
        if mode:
            self._invalidate_score_cache()
        return super().train(mode)

    def wire(self, ui_graph: sp.csr_matrix, *, feature_dim: int | None = None) -> None:
        """Attach the downstream ranker named by ``config.recommend.kind``.

        The ranker is initialized under ``config.seed``. Whatever
        graph-derived state it needs is prepared here rather than on the first
        scoring call: a propagation-based ranker gets its normalized adjacency
        cached, and a popularity ranker gets fitted.

        Args:
            ui_graph: Bipartite ``(users, items)`` interaction matrix.
            feature_dim: Width of the completion output that will be handed to
                the ranker, for rankers that can consume it. Leave as ``None``
                to rank from ID embeddings and the graph alone.

        Raises:
            Cfg: If ``config.recommend.kind`` is not registered.
        """
        users = ui_graph.shape[0]
        items = ui_graph.shape[1]
        self.ui_graph = ui_graph.tocsr(copy=True)
        recommender = build_recommend(
            self.config.recommend.kind,
            users=users,
            items=items,
            embed=self.config.recommend.embed,
            layers=self.config.recommend.layers,
            feature_dim=feature_dim,
            seed=self.config.seed,
        )
        if isinstance(recommender, Normalizes):
            recommender.normalize(ui_graph)
        if isinstance(recommender, Fits):
            recommender.fit(ui_graph)
        self.recommender = recommender

    def attach(
        self,
        features: dict[str, np.ndarray],
        mask: np.ndarray,
        adjacency: sp.csr_matrix | None = None,
    ) -> None:
        """Bind full-graph data for on-the-fly retrieval.

        The boundary owns immutable snapshots of the supplied arrays and
        sparse matrix. Callers may therefore reuse or mutate their input
        buffers without changing a live serving pipeline behind its back.

        Raises:
        ValueError: If feature names, shapes, mask dimensions, or adjacency
            dimensions do not match the configured corpus.
        """
        if not features:
            raise ValueError("features must contain at least one modality")
        expected = set(self.dims)
        actual = set(features)
        if actual != expected:
            missing = ", ".join(sorted(expected - actual)) or "-"
            extra = ", ".join(sorted(actual - expected)) or "-"
            raise ValueError(f"feature modalities mismatch: missing={missing}, extra={extra}")
        count: int | None = None
        snapshot: dict[str, np.ndarray] = {}
        for name, width in self.dims.items():
            value = np.asarray(features[name])
            if value.ndim != 2 or value.shape[1] != width:
                raise ValueError(
                    f"feature {name!r} must have shape (items, {width}), got {value.shape}"
                )
            if count is None:
                count = int(value.shape[0])
            elif value.shape[0] != count:
                raise ValueError("all feature modalities must contain the same item count")
            snapshot[name] = np.array(value, dtype=np.float32, copy=True, order="C")
        mask_snapshot = np.array(mask, dtype=np.float32, copy=True, order="C")
        if mask_snapshot.ndim != 2 or mask_snapshot.shape != (count, len(self.dims)):
            raise ValueError(
                f"mask must have shape ({count}, {len(self.dims)}), got {mask_snapshot.shape}"
            )
        if adjacency is not None:
            adjacency_snapshot = adjacency.tocsr(copy=True)
            if adjacency_snapshot.shape != (count, count):
                raise ValueError(
                    f"adjacency must have shape ({count}, {count}), got {adjacency_snapshot.shape}"
                )
        else:
            adjacency_snapshot = None
        self.cfeat = snapshot
        self.cmask = mask_snapshot
        self.cadj = adjacency_snapshot
        self._invalidate_score_cache()

    @torch.no_grad()
    def score(self, users: torch.Tensor, items: torch.Tensor) -> torch.Tensor:
        """Score users against items using attached corpus and completion state.

        This is the serving-safe ranking path. It refuses to fall back to
        ID-only scores when the corpus or interaction graph is missing, and it
        feeds completed item representations into rankers that support them.

        Args:
            users: User ids with shape ``(B_u,)``.
            items: Item ids with shape ``(B_i,)``.

        Returns:
            Score matrix with shape ``(B_u, B_i)``.

        Raises:
            Model: If the pipeline has not been wired or attached.
        """
        if self.recommender is None or self.ui_graph is None:
            raise Model("pipeline has no wired recommender and user-item graph")
        if self.cfeat is None or self.cmask is None or self.cadj is None:
            raise Model("pipeline has no attached feature corpus and item graph")
        model_device = next(self.parameters()).device
        users = users.to(model_device)
        items = items.to(model_device)
        if not self.cfeat:
            raise Model("pipeline feature corpus is empty")
        first = next(iter(self.cfeat.values()))
        count = int(first.shape[0])
        if any(int(value.shape[0]) != count for value in self.cfeat.values()):
            raise Model("pipeline feature corpus has inconsistent item counts")
        cached = self._score_cache
        if cached is None or cached[0] != model_device:
            index = torch.arange(count, dtype=torch.long, device=model_device)
            features = {
                name: torch.from_numpy(np.asarray(value, dtype=np.float32)).to(model_device)
                for name, value in self.cfeat.items()
            }
            mask = torch.from_numpy(np.asarray(self.cmask, dtype=np.float32)).to(model_device)
            output = self(features, mask, self.cadj, index=index, training=False)
            completed = torch.cat([output.completed[name] for name in self.dims], dim=-1)
            self._score_cache = (model_device, completed)
        else:
            completed = cached[1]
        recommender = self.recommender
        graph = None if isinstance(recommender, Normalizes) else self.ui_graph
        if isinstance(recommender, FeatureAware):
            return recommender.score_with_features(users, items, graph, completed)
        return cast(torch.Tensor, recommender(users, items, graph))

    def forward(
        self,
        features: dict[str, torch.Tensor],
        mask: torch.Tensor,
        adjacency: sp.spmatrix,
        index: torch.Tensor | None = None,
        training: bool = True,
    ) -> Output:
        """End-to-end forward pass.

        Args:
            features: Per-modality features ``(B, d_m)``.
            mask: ``(B, M)`` availability.
            adjacency: Sparse item-item adjacency.
            index: Optional ``(B,)`` item ids for retrieval.
            training: Whether the pass is stochastic. This governs *all*
                stochastic components, not just Gumbel noise: the encoder's
                dropout layers are switched to match for the duration of the
                call and restored afterwards. Pass ``False`` for inference to
                get a deterministic, dropout-free result.

        Returns:
            Output with completed modalities, routing weights, and (when
            retrieval buffers are set) the subgraph indices used.

        Raises:
            Net: If the adjacency has self-loops. Build the item graph
                once with ``morel.data.build.cooccurrence``; that
                builder removes self-loops before persisting.
        """
        if adjacency.diagonal().any():
            raise Net(
                "Pipeline.forward received an adjacency with self-loops; "
                "build the item graph once with "
                "morel.data.build.cooccurrence (which removes them) "
                "and pass that adjacency here."
            )
        with mode(self, training):
            device = features[next(iter(features))].device
            pe_full = self.encoder(adjacency).to(device)
            # Pad PE up to configured pe_dim if the graph is too small to provide
            # the requested number of nontrivial eigenvectors.
            if pe_full.shape[-1] < self.config.encode.pe:
                pad = torch.zeros(
                    *pe_full.shape[:-1],
                    self.config.encode.pe - pe_full.shape[-1],
                    device=device,
                    dtype=pe_full.dtype,
                )
                pe_full = torch.cat([pe_full, pad], dim=-1)
            subgraph_indices: np.ndarray | None = None
            subgraph_mask: np.ndarray | None = None

            if self.cfeat is not None and self.cmask is not None and index is not None:
                queries = [int(i) for i in index.detach().cpu().tolist()]
                result = batch(
                    queries,
                    self.cfeat,
                    self.cmask,
                    self.cadj if self.cadj is not None else sp.csr_matrix(adjacency),
                    anchors=self.config.retrieve.anchors,
                    iters=self.config.retrieve.iters,
                    kind=self.config.retrieve.kind,
                    max_nodes=self._retrieval_max_nodes,
                )
                subgraph_indices = result.nodes
                subgraph_mask = result.mask
                hidden = self.encode(
                    features,
                    mask,
                    pe_full,
                    result,
                    device=device,
                )
            else:
                batch_size = mask.shape[0]
                pe_batch = pe_full[index] if index is not None else pe_full[:batch_size]
                hidden = self.transformer(features, mask, pe_batch)

            quantized, routing = self.codebook(hidden, training=training)
            completed = self.decoders(quantized, mask=mask)
        return Output(
            completed=completed,
            routing=routing,
            subgraph_indices=subgraph_indices,
            subgraph_mask=subgraph_mask,
        )

    def encode(
        self,
        features: dict[str, torch.Tensor],
        mask: torch.Tensor,
        pe_full: torch.Tensor,
        result: Result,
        *,
        device: torch.device,
    ) -> torch.Tensor:
        """Encode each query item with its retrieved subgraph as one padded batch.

        All per-query subgraphs are padded to ``result.cap`` and processed
        in a single transformer call with a batched attention mask, instead of
        one Python loop iteration per query. Empty subgraphs are padded with a
        single attention-masked token so the transformer still produces one
        embedding per query.

        Raises:
            Model: If no corpus has been attached. Call
                :meth:`attach` before encoding subgraphs.
        """
        corpus_features = self.cfeat
        corpus_mask = self.cmask
        if corpus_features is None or corpus_mask is None:
            raise Model(
                "encode needs a bound corpus; call Pipeline.attach(features, mask, adjacency) first"
            )
        peak = max(int(result.cap), 1)
        batch = int(result.batch)
        modalities = list(self.dims.keys())
        # ``Result.nodes`` is already a padded, rectangular index matrix. A
        # single gather per modality replaces the previous query/modality
        # Python loops; invalid padded positions remain harmless because the
        # attention mask excludes them below.
        if result.cap:
            node_ids = torch.from_numpy(result.nodes).long().to(device)
            node_features = {
                name: torch.from_numpy(corpus_features[name][result.nodes]).to(
                    device=device, dtype=torch.float32
                )
                for name in modalities
            }
            node_mask = torch.from_numpy(corpus_mask[result.nodes]).to(
                device=device, dtype=torch.float32
            )
            pe = pe_full[node_ids]
            attention = torch.from_numpy(result.mask).bool().to(device)
        else:
            node_features = {
                name: torch.zeros(batch, peak, self.dims[name], device=device)
                for name in modalities
            }
            node_mask = torch.zeros(batch, peak, len(modalities), device=device)
            pe = torch.zeros(batch, peak, pe_full.shape[-1], device=device)
            attention = torch.zeros(batch, peak, dtype=torch.bool, device=device)
        empty = torch.from_numpy(result.sizes == 0).to(device)
        if bool(empty.any()):
            attention[empty, 0] = True
            node_mask[empty, 0, :] = 1.0

        hidden: torch.Tensor = self.transformer(
            node_features,
            node_mask,
            pe,
            attention_mask=attention,
            sequence=True,
        )
        return hidden


__all__ = ["Output", "Pipeline", "mode"]
