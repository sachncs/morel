"""LightGCN downstream recommender with cached normalized adjacency."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn

from morel.core.errors import Model
from morel.core.seed import deterministic
from morel.recommend.protocol import RecommenderCapabilities


@dataclass(frozen=True)
class _AdjacencyCache:
    """Owned, content-addressed normalized adjacency state.

    The cache is deliberately not a registered module buffer: it is derived
    from caller-owned corpus data and should not be serialized as model
    weights. ``Light._apply`` migrates its tensor whenever the module moves
    device or dtype, and :meth:`Light.invalidate_cache` is the explicit
    lifecycle boundary for corpus replacement.
    """

    graph_key: str
    tensor: torch.Tensor

    def __iter__(self) -> Iterator[str | torch.Tensor]:
        """Retain the historical ``key, tensor = light.cache`` interface."""
        yield self.graph_key
        yield self.tensor

    def __getitem__(self, index: int) -> str | torch.Tensor:
        """Retain tuple-style compatibility access for old integrations."""
        if index == 0:
            return self.graph_key
        if index == 1:
            return self.tensor
        raise IndexError(index)


def key(matrix: sp.csr_matrix) -> str:
    """Stable SHA256 of a CSR matrix's nonzero pattern and shape."""
    coo = sp.coo_matrix(matrix)
    h = hashlib.sha256()
    h.update(np.asarray(coo.shape, dtype=np.int64).tobytes())
    h.update(coo.data.astype(np.float32, copy=False).tobytes())
    h.update(coo.row.astype(np.int64, copy=False).tobytes())
    h.update(coo.col.astype(np.int64, copy=False).tobytes())
    return h.hexdigest()


class Light(nn.Module):
    """LightGCN: linear message passing with mean aggregation.

    The normalized bipartite adjacency is built once on first forward and
    cached, so ``ui_graph`` does not need to be passed at every call unless
    it changes. The cache key is a content hash of the CSR matrix, not its
    ``id()`` (which can be reused after GC).

    Attributes:
        users: Number of users.
        items: Number of items.
        user_emb: User embedding layer.
        item_emb: Item embedding layer.
        cache: Owned normalized adjacency cache, or ``None`` before wiring.
    """

    capabilities = RecommenderCapabilities(item_features=True, normalizes=True, fits=False)

    def __init__(
        self,
        users: int,
        items: int,
        *,
        embed: int = 64,
        layers: int = 3,
        feature_dim: int | None = None,
        seed: int | None = None,
    ) -> None:
        """Build a LightGCN ranker.

        Args:
            users: Number of users; must be positive.
            items: Number of items; must be positive.
            embed: Embedding width.
            layers: Number of propagation steps; must be non-negative.
            feature_dim: Width of the modality features that will be supplied
                to :meth:`forward`. When set, a projection into the embedding
                space is created so the completion stage's output can inform
                ranking. Leave as ``None`` for ID-embeddings only.
            seed: If given, initialize the embeddings under this seed so that
                two ``Light`` instances built with the same seed hold
                identical weights. The caller's global RNG state is left
                untouched. If ``None``, the global RNG is used and the
                weights depend on ambient process state.
        """
        super().__init__()
        if users <= 0 or items <= 0:
            raise ValueError("users and items must be positive")
        if layers < 0:
            raise ValueError(f"layers must be non-negative, got {layers}")
        self.users = users
        self.items = items
        self.layers = layers
        self.embed = embed
        with nullcontext() if seed is None else deterministic(seed):
            self.user_emb = nn.Embedding(users, embed)
            self.item_emb = nn.Embedding(items, embed)
            nn.init.xavier_uniform_(self.user_emb.weight)
            nn.init.xavier_uniform_(self.item_emb.weight)
            self.fproj: nn.Linear | None = None
            if feature_dim is not None:
                if feature_dim <= 0:
                    raise ValueError(f"feature_dim must be positive, got {feature_dim}")
                self.fproj = nn.Linear(feature_dim, embed)
        self.fdim = feature_dim
        self.cache: _AdjacencyCache | None = None

    def _apply(self, fn: Any, recurse: bool = True) -> nn.Module:
        """Apply a module migration to derived adjacency state as well.

        PyTorch applies ``Module.to``/``cuda`` only to parameters and
        registered buffers. The normalized adjacency is intentionally not a
        serialized buffer, so it must be migrated explicitly to prevent a
        stale CPU/GPU tensor after a model move.
        """
        super()._apply(fn, recurse)  # type: ignore[no-untyped-call]
        if self.cache is not None:
            self.cache = _AdjacencyCache(self.cache.graph_key, fn(self.cache.tensor))
        return self

    def invalidate_cache(self) -> None:
        """Drop graph-derived state after replacing the attached corpus."""
        self.cache = None

    def forward(
        self,
        users: torch.Tensor,
        items: torch.Tensor,
        ui_graph: sp.csr_matrix | None = None,
        item_features: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Score ``users`` against ``items`` via L-step LightGCN propagation.

        Args:
            users: ``(B_u,)`` long tensor of user ids.
            items: ``(B_i,)`` long tensor of item ids.
            ui_graph: Optional new bipartite graph; uses cached one if None.
            item_features: Optional ``(items, feature_dim)`` modality
                representations -- in this pipeline, the output of the
                completion stage. When given, they are projected into the
                embedding space and added to the item embeddings before
                propagation, so that completing a missing modality actually
                changes what gets recommended. Requires ``feature_dim`` to
                have been set on the constructor.

        Returns:
            ``(B_u, B_i)`` score matrix.

        Raises:
            Model: If ``item_features`` is supplied but no projection was
                configured, or if its shape does not match.
        """
        if users.ndim != 1 or items.ndim != 1:
            raise ValueError("users and items must be 1-D id tensors")
        if users.numel() == 0 or items.numel() == 0:
            return torch.empty(
                (users.shape[0], items.shape[0]),
                dtype=self.user_emb.weight.dtype,
                device=self.user_emb.weight.device,
            )
        if users.min() < 0 or users.max() >= self.users:
            raise IndexError(f"user indices must be in [0, {self.users})")
        if items.min() < 0 or items.max() >= self.items:
            raise IndexError(f"item indices must be in [0, {self.items})")
        adj_norm = self.normalize(ui_graph)
        item_emb = self.item_emb.weight
        if item_features is not None:
            if self.fproj is None:
                raise Model(
                    "item_features was passed but Light was built without "
                    "feature_dim; construct it with feature_dim set to the "
                    "width of the completion output"
                )
            if item_features.shape[0] != self.items:
                raise Model(
                    f"item_features has {item_features.shape[0]} rows, expected {self.items}"
                )
            item_emb = item_emb + self.fproj(item_features.to(item_emb.dtype))
        all_emb = torch.cat([self.user_emb.weight, item_emb], dim=0)
        stack = [all_emb]
        for _ in range(self.layers):
            all_emb = torch.sparse.mm(adj_norm, all_emb)
            stack.append(all_emb)
        final = torch.stack(stack, dim=0).mean(dim=0)
        u_emb = final[: self.users]
        i_emb = final[self.users :]
        return u_emb[users] @ i_emb[items].t()

    def score_with_features(
        self,
        users: torch.Tensor,
        items: torch.Tensor,
        ui_graph: sp.csr_matrix | None,
        item_features: torch.Tensor,
    ) -> torch.Tensor:
        """Score with completed item features through the explicit capability."""
        return self.forward(users, items, ui_graph, item_features=item_features)

    def normalize(self, ui_graph: sp.csr_matrix | None) -> torch.Tensor:
        """Compute or fetch the cached normalized adjacency tensor.

        Behaviour:
        - if ``ui_graph is None`` and the cache is populated, return the
          cached tensor (after a device-mismatch move);
        - if ``ui_graph`` matches the cached content hash, return the cached
          tensor;
        - otherwise rebuild from scratch.

        Args:
            ui_graph: New bipartite CSR, or ``None`` to use the cache.

        Returns:
            Sparse ``(users + items, users + items)`` tensor on the model's
            device.

        Raises:
            ValueError: If ``ui_graph is None`` and the cache is empty.
        """
        if ui_graph is None and self.cache is not None:
            cached = self.cache.tensor
            if cached.device != self.user_emb.weight.device:
                cached = cached.to(self.user_emb.weight.device)
                self.cache = _AdjacencyCache(self.cache.graph_key, cached)
            return cached
        if ui_graph is None:
            raise ValueError("ui_graph is required on the first call")
        k = key(ui_graph)
        if self.cache is not None and self.cache.graph_key == k:
            cached = self.cache.tensor
            if cached.device != self.user_emb.weight.device:
                cached = cached.to(self.user_emb.weight.device)
                self.cache = _AdjacencyCache(k, cached)
            return cached
        top = sp.hstack([sp.csr_matrix((self.users, self.users)), ui_graph])
        bottom = sp.hstack([ui_graph.T, sp.csr_matrix((self.items, self.items))])
        adj = sp.vstack([top, bottom]).tocoo()
        rowsum = np.asarray(adj.sum(axis=1)).flatten()
        with np.errstate(divide="ignore"):
            d_inv_sqrt = np.where(rowsum > 0, np.power(rowsum, -0.5), 0.0)
        d_mat = sp.diags(d_inv_sqrt.astype(np.float32))
        normalized = (d_mat @ adj @ d_mat).tocoo()
        # Drop explicit zeros (which can arise from rowsum==0 deg-zero
        # nodes) before handing the array to torch; sparse_coo_tensor
        # raises a warning on stored zeros because they violate
        # invariants the constructor cannot satisfy.
        normalized = normalized.tocsr()
        normalized.eliminate_zeros()
        normalized = normalized.tocoo()
        indices = torch.from_numpy(np.vstack((normalized.row, normalized.col))).long()
        values = torch.from_numpy(normalized.data).float()
        shape = torch.Size(normalized.shape)
        # Opt into runtime invariant checks; this also prevents torch from
        # emitting the "Sparse invariant checks are implicitly disabled"
        # warning. We construct well-formed tensors, so the cost is
        # negligible.
        with torch.sparse.check_sparse_tensor_invariants():  # type: ignore[no-untyped-call]  # torch stubs leave this untyped
            tensor = torch.sparse_coo_tensor(indices, values, shape).coalesce()
        target_device = self.user_emb.weight.device
        if tensor.device != target_device:
            tensor = tensor.to(target_device)
        self.cache = _AdjacencyCache(k, tensor)
        return tensor


__all__ = ["Light"]
