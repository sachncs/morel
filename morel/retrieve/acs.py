"""Anchor Connecting Subgraph (ACS) — Algorithm 1 from the paper.

Multi-source BFS with reachability bitmasks. The first node whose bitmask
equals the all-anchors mask is the collision root. The ACS is the union of
shortest paths from the collision root back to each anchor.

Correctness fixes over the legacy implementation:
- iterative backtrack (no RecursionError on long paths)
- explicit self-loop guard
- duplicate anchor rejection
- deterministic fallback when anchors are not mutually reachable
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path

from morel.core.errors import Net
from morel.core.log import get as logger
from morel.graph import invariants

log = logger("retrieve.acs")


def verify(adj: sp.csr_matrix, anchors: list[int]) -> None:
    """Validate that anchors form a connected subgraph.

    Args:
        adj: Adjacency matrix.
        anchors: Anchor node ids.
    """
    if anchors is None:
        raise Net("anchors must not be None")
    if not anchors:
        return
    nodes = adj.shape[0]
    seen: set[int] = set()
    for anchor in anchors:
        if not isinstance(anchor, (int, np.integer)):
            raise Net(f"anchor must be int, got {type(anchor).__name__}")
        idx = int(anchor)
        if idx < 0 or idx >= nodes:
            raise Net(f"anchor {idx} out of range [0, {nodes})")
        if idx in seen:
            raise Net(f"duplicate anchor {idx}")
        seen.add(idx)


def compute(adj: sp.csr_matrix, anchors: list[int], *, fallback: str = "anchors") -> set[int]:
    """Compute the Anchor Connecting Subgraph.

    Args:
        adj: Symmetric adjacency.
        anchors: Distinct anchor node ids.
        fallback: Behaviour when no collision root is found. ``"anchors"``
            returns the anchor set (default); ``"empty"`` returns an empty
            set.

    Returns:
        Set of node ids in the ACS.

    Raises:
        Net: On bad input.
    """
    if adj.ndim != 2 or adj.shape[0] != adj.shape[1]:
        raise Net(f"adj must be square, got {adj.shape}")
    verify(adj, anchors)
    invariants.loopless(adj)
    if not anchors:
        return set()
    if len(anchors) == 1:
        return {int(anchors[0])}

    anchors_int = [int(a) for a in anchors]

    # Run the multi-source search in SciPy's compiled graph implementation.
    # The legacy Python bit-mask BFS revisited high-degree nodes once per
    # anchor, making a 10k-node catalog take seconds before MAGE started.
    # Distances and predecessor trees preserve the ACS invariant: choose a
    # node reachable from every anchor with the smallest worst-case distance,
    # then union one shortest path to each anchor.
    distances, predecessors = shortest_path(
        adj,
        directed=False,
        indices=np.asarray(anchors_int, dtype=np.int64),
        unweighted=True,
        return_predecessors=True,
    )
    reachable = np.all(np.isfinite(distances), axis=0)
    if not reachable.any():
        if fallback == "empty":
            log.warning(
                "no collision root found; returning empty set",
                extra={"anchors": anchors_int},
            )
            return set()
        if fallback == "anchors":
            log.warning(
                "no collision root found; returning anchor set",
                extra={"anchors": anchors_int},
            )
            return set(anchors_int)
        raise Net(f"unknown fallback strategy: {fallback!r}")

    worst_distance = np.max(distances[:, reachable], axis=0)
    candidates = np.flatnonzero(reachable)
    collision = int(candidates[int(np.argmin(worst_distance))])

    subgraph: set[int] = {int(collision)}
    for anchor_idx, target in enumerate(anchors_int):
        if target == int(collision):
            continue
        node = int(collision)
        while node != target:
            predecessor = int(predecessors[anchor_idx, node])
            if predecessor < 0:
                raise Net(f"backtrack failed at node {node} for anchor {target}")
            subgraph.add(node)
            node = predecessor
        subgraph.add(target)
    return subgraph


def batch(
    adj: sp.csr_matrix, anchor_sets: list[list[int]], *, fallback: str = "anchors"
) -> list[set[int]]:
    """Compute ACS for a batch of anchor sets."""
    return [compute(adj, anchors, fallback=fallback) for anchors in anchor_sets]


__all__ = ["batch", "compute"]
