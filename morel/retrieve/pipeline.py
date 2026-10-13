"""Retrieval pipeline: anchor retrieval + ACS + MAGE in one call.

The single-query path is exposed as ``retrieve`` and is the workhorse called
from the model. The batch path returns padded index tensors plus an attention
mask for downstream sequence models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
import scipy.sparse as sp
import torch

from morel.core.errors import Cfg, Net
from morel.retrieve.acs import compute as acs_compute
from morel.retrieve.anchor import AnchorIndex
from morel.retrieve.anchor import prepare as prepare_anchor
from morel.retrieve.anchor import query as anchor_query
from morel.retrieve.bfs import bfs as bfs_distances
from morel.retrieve.mage import expand as mage_expand
from morel.retrieve.relevance import RelevanceIndex, prepare


@runtime_checkable
class RetrievalStrategy(Protocol):
    """Callable contract shared by every registered retrieval strategy."""

    def __call__(
        self,
        query: int,
        features: dict[str, np.ndarray],
        mask: np.ndarray,
        adj: sp.csr_matrix,
        *,
        anchors: int,
        iters: int,
        fallback: str,
        relevance_index: RelevanceIndex | None = None,
        anchor_index: AnchorIndex | None = None,
        max_nodes: int | None = None,
    ) -> set[int]:
        """Return a subgraph containing the requested query item."""


@dataclass(frozen=True)
class Result:
    """Retrieval output for one query or a batch.

    Attributes:
        nodes: Padded node indices.
        sizes: Actual number of nodes per batch item.
        mask: Boolean mask for valid nodes.
    """

    nodes: np.ndarray  # (B, max_S) int64
    sizes: np.ndarray  # (B,) int64
    mask: np.ndarray  # (B, max_S) bool, True = real node

    @property
    def batch(self) -> int:
        """Return the batch size."""
        return int(self.sizes.shape[0])

    @property
    def cap(self) -> int:
        """Return the maximum subgraph size."""
        return int(self.nodes.shape[1])


def for_q(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    *,
    anchors: int,
    anchor_index: AnchorIndex | None = None,
) -> set[int]:
    """Return the cosine-nearest anchors of ``query`` across observed modalities."""
    observed = [name for idx, name in enumerate(features.keys()) if mask[query, idx] > 0]
    found: set[int] = set()
    for name in observed:
        found.update(
            int(a)
            for a in anchor_query(query, name, features, mask, top=anchors, index=anchor_index)
        )
    return found


def mage(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int,
    iters: int,
    fallback: str,
    relevance_index: RelevanceIndex | None = None,
    anchor_index: AnchorIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Anchor retrieval followed by MAGE expansion; the method's default."""
    anchor_set = for_q(query, features, mask, anchors=anchors, anchor_index=anchor_index)
    if not anchor_set:
        return {int(query)}
    return mage_expand(
        adj,
        list(anchor_set),
        query,
        features,
        mask,
        iters=iters,
        fallback=fallback,
        relevance_index=relevance_index,
        max_nodes=max_nodes,
    )


def acs(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int,
    iters: int,
    fallback: str,
    relevance_index: RelevanceIndex | None = None,
    anchor_index: AnchorIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Anchor retrieval followed by the Anchor Connecting Subgraph, without MAGE."""
    anchor_set = for_q(query, features, mask, anchors=anchors, anchor_index=anchor_index)
    if not anchor_set:
        return {int(query)}
    return acs_compute(adj, sorted(anchor_set), fallback=fallback)


def anchor(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int,
    iters: int,
    fallback: str,
    relevance_index: RelevanceIndex | None = None,
    anchor_index: AnchorIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Anchors only, with no graph expansion; the no-expansion ablation."""
    return for_q(query, features, mask, anchors=anchors, anchor_index=anchor_index)


def bfs(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int,
    iters: int,
    fallback: str,
    relevance_index: RelevanceIndex | None = None,
    anchor_index: AnchorIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Graph neighbourhood of the query within ``iters`` hops, ignoring features.

    Uses only the graph, so subgraph selection does not depend on the modality
    features at all.
    """
    distances = bfs_distances(adj, [int(query)])
    return {int(node) for node, hops in distances.items() if hops <= max(int(iters), 1)}


def none(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int,
    iters: int,
    fallback: str,
    relevance_index: RelevanceIndex | None = None,
    anchor_index: AnchorIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Return the query alone: the no-retrieval ablation.

    Nothing is retrieved, so the encoder sees only the item being completed
    and no graph context. This is the condition ``eval.ablations`` calls
    ``noretry``.
    """
    return {int(query)}


#: Map from config name to strategy function. Module-local; no global registry.
KIND: dict[str, RetrievalStrategy] = {
    "mage": mage,
    "acs": acs,
    "anchor": anchor,
    "bfs": bfs,
    "none": none,
}


def retrieve(
    query: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int = 10,
    iters: int = 10,
    fallback: str = "anchors",
    kind: str = "mage",
    relevance_index: RelevanceIndex | None = None,
    anchor_index: AnchorIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Retrieve and expand a subgraph for one query item.

    Args:
        query: Item id to build a subgraph around.
        features: Per-modality feature arrays.
        mask: ``(items, modalities)`` availability.
        adj: Symmetric item-item adjacency.
        anchors: Number of cosine neighbours per observed modality.
        iters: Expansion budget, interpreted by the strategy.
        fallback: Behaviour when expansion finds no collision root.
        kind: Registered retrieval strategy; see ``morel.retrieve.KIND``.
        relevance_index: Optional precomputed relevance index.
        anchor_index: Optional precomputed normalized anchor index.
        max_nodes: Optional upper bound on the returned subgraph size.

    Returns:
        Node ids of the retrieved subgraph, always including ``query``.

    Raises:
        Cfg: If ``kind`` is not a registered strategy.
    """
    if kind not in KIND:
        raise Cfg(
            f"unknown retrieval strategy {kind!r}; available: {', '.join(sorted(KIND)) or '(none)'}"
        )
    strategy = KIND[kind]
    observed = [name for idx, name in enumerate(features.keys()) if mask[query, idx] > 0]
    if not observed and kind != "bfs":
        return {int(query)}
    subgraph = strategy(
        query,
        features,
        mask,
        adj,
        anchors=anchors,
        iters=iters,
        fallback=fallback,
        relevance_index=relevance_index,
        anchor_index=anchor_index,
        max_nodes=max_nodes,
    )
    subgraph = set(subgraph)
    subgraph.add(int(query))
    if max_nodes is not None and len(subgraph) > max_nodes:
        raise Net(
            f"retrieved subgraph has {len(subgraph)} nodes, exceeding serving budget {max_nodes}"
        )
    return subgraph


def batch(
    queries: list[int],
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    adj: sp.csr_matrix,
    *,
    anchors: int = 10,
    iters: int = 10,
    fallback: str = "anchors",
    kind: str = "mage",
    max_nodes: int | None = None,
) -> Result:
    """Batched retrieval that returns padded tensors for downstream models."""
    relevance_index = prepare(features, mask) if kind == "mage" else None
    anchor_index = prepare_anchor(features, mask) if queries else None
    subgraphs = [
        retrieve(
            q,
            features,
            mask,
            adj,
            anchors=anchors,
            iters=iters,
            fallback=fallback,
            kind=kind,
            relevance_index=relevance_index,
            anchor_index=anchor_index,
            max_nodes=max_nodes,
        )
        for q in queries
    ]
    sizes = np.array([len(s) for s in subgraphs], dtype=np.int64)
    cap = int(sizes.max()) if sizes.size else 0
    nodes = np.zeros((len(queries), cap), dtype=np.int64)
    valid = np.zeros((len(queries), cap), dtype=bool)
    for i, sg in enumerate(subgraphs):
        arr = np.array(sorted(sg), dtype=np.int64)
        nodes[i, : arr.size] = arr
        valid[i, : arr.size] = True
    return Result(nodes=nodes, sizes=sizes, mask=valid)


def cast(
    result: Result, *, device: str | torch.device | None = None
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Convert a batched Result into (nodes, mask, sizes) torch tensors."""
    nodes = torch.from_numpy(result.nodes).long()
    mask_t = torch.from_numpy(result.mask).bool()
    sizes = torch.from_numpy(result.sizes).long()
    if device is not None:
        nodes = nodes.to(device)
        mask_t = mask_t.to(device)
        sizes = sizes.to(device)
    return nodes, mask_t, sizes


__all__ = ["Cfg", "Result", "batch", "cast", "retrieve"]
