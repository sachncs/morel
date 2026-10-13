"""Modality-Aware Graph Expansion (MAGE) — Algorithm 2 from the paper.

Greedy boundary add/remove that maximizes mean relevance while preserving
connectivity and all anchors.

Correctness fixes over the legacy implementation:
- best-improvement hill climbing (canonical Algorithm 2)
- sorted boundary iteration (deterministic across runs)
- cached neighbor arrays (no O(N) neighbor rebuild per iteration)
- iterative bounds checking
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import scipy.sparse as sp

from morel.core.errors import Net
from morel.core.log import get as logger
from morel.retrieve.acs import compute as acs_compute
from morel.retrieve.relevance import RelevanceIndex, prepare

log = logger("retrieve.mage")


def _neighbor_rows(adj: sp.csr_matrix, nodes: set[int]) -> dict[int, np.ndarray]:
    """Materialize sorted adjacency rows only for the supplied nodes."""
    result: dict[int, np.ndarray] = {}
    for node in nodes:
        start = adj.indptr[node]
        end = adj.indptr[node + 1]
        result[node] = np.sort(adj.indices[start:end].astype(np.int64, copy=False))
    return result


def boundary(subgraph: set[int], neighbors: dict[int, np.ndarray]) -> list[int]:
    """Return the sorted list of nodes adjacent to ``subgraph`` but not in it."""
    boundary: set[int] = set()
    for node in subgraph:
        for neighbor in neighbors.get(node, ()):
            if neighbor not in subgraph:
                boundary.add(int(neighbor))
    return sorted(boundary)


def neighbors(
    subgraph_nodes: np.ndarray, neighbors: dict[int, np.ndarray]
) -> dict[int, np.ndarray]:
    """Build a neighbor lookup restricted to ``subgraph_nodes``."""
    set_nodes = set(subgraph_nodes.tolist())
    return {
        int(node): np.array(
            [int(n) for n in neighbors.get(int(node), ()) if int(n) in set_nodes],
            dtype=np.int64,
        )
        for node in subgraph_nodes
    }


def _articulation_points(
    subgraph_nodes: set[int], parent_neighbors: dict[int, np.ndarray]
) -> set[int]:
    """Return cut vertices of a connected induced subgraph.

    This is an iterative Tarjan traversal. MAGE may evaluate thousands of
    removal candidates per query; checking connectivity with a fresh BFS for
    every candidate is quadratic in the subgraph size. One articulation-point
    pass gives the same removal decision in linear time and avoids recursion
    depth limits on long catalog graphs.
    """
    if len(subgraph_nodes) < 3:
        return set()
    discovery: dict[int, int] = {}
    low: dict[int, int] = {}
    parent: dict[int, int | None] = {}
    children: dict[int, int] = {}
    points: set[int] = set()
    clock = 0

    for root in sorted(subgraph_nodes):
        if root in discovery:
            continue
        clock += 1
        discovery[root] = low[root] = clock
        parent[root] = None
        children[root] = 0
        root_iter = (int(n) for n in parent_neighbors.get(root, ()))
        stack: list[tuple[int, Iterator[int]]] = [(root, root_iter)]
        while stack:
            node, iterator = stack[-1]
            try:
                neighbor = next(iterator)
            except StopIteration:
                stack.pop()
                predecessor = parent[node]
                if predecessor is None:
                    if children[node] > 1:
                        points.add(node)
                    continue
                low[predecessor] = min(low[predecessor], low[node])
                if parent[predecessor] is not None and low[node] >= discovery[predecessor]:
                    points.add(predecessor)
                continue
            if neighbor not in subgraph_nodes or neighbor == parent[node]:
                continue
            if neighbor not in discovery:
                parent[neighbor] = node
                children[node] += 1
                clock += 1
                discovery[neighbor] = low[neighbor] = clock
                children[neighbor] = 0
                neighbor_iter = (int(n) for n in parent_neighbors.get(neighbor, ()))
                stack.append((neighbor, neighbor_iter))
                continue
            low[node] = min(low[node], discovery[neighbor])
    return points


def expand(
    adj: sp.csr_matrix,
    anchors: list[int],
    query_item: int,
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    *,
    iters: int = 10,
    fallback: str = "anchors",
    relevance_index: RelevanceIndex | None = None,
    max_nodes: int | None = None,
) -> set[int]:
    """Run MAGE greedy expansion.

    Args:
        adj: Symmetric item-item adjacency.
        anchors: Anchor set from anchor retrieval.
        query_item: Query node id.
        features: Per-modality feature arrays.
        mask: Modality availability mask.
        iters: Maximum greedy iterations.
        fallback: ACS fallback strategy.
        relevance_index: Optional precomputed relevance index.
        max_nodes: Optional upper bound on the returned subgraph size.

    Returns:
        Set of node ids in the expanded subgraph.
    """
    if iters <= 0:
        raise Net(f"iters must be positive, got {iters}")
    anchors_int = [int(a) for a in anchors]
    if query_item not in anchors_int:
        anchors_int = sorted({*anchors_int, int(query_item)})

    subgraph_set = acs_compute(adj, anchors_int, fallback=fallback)
    if not subgraph_set:
        subgraph_set = set(anchors_int)
    subgraph_set.add(int(query_item))
    if max_nodes is not None and len(subgraph_set) > max_nodes:
        raise Net(
            f"retrieved subgraph has {len(subgraph_set)} nodes, "
            f"exceeding serving budget {max_nodes}"
        )
    # MAGE only needs adjacency rows for the current subgraph and newly added
    # boundary nodes. Building a dictionary for every catalog node here made
    # each query O(catalog size) before the actual expansion began.
    neighbor_map = _neighbor_rows(adj, subgraph_set)
    relevance = relevance_index if relevance_index is not None else prepare(features, mask)
    best_score = relevance.score(query_item, np.array(sorted(subgraph_set), dtype=np.int64))

    for _ in range(iters):
        changed = False
        boundary_list = boundary(subgraph_set, neighbor_map)
        best_candidate: int | None = None
        best_candidate_score = best_score
        for node in boundary_list:
            trial = subgraph_set | {node}
            # Every boundary node is adjacent to the current connected
            # subgraph by construction, so adding it cannot disconnect the
            # trial. Avoid a full BFS for every candidate; connectivity still
            # must be checked for removals below.
            score = relevance.score(query_item, np.array(sorted(trial), dtype=np.int64))
            if score > best_candidate_score + 1e-12:
                best_candidate = node
                best_candidate_score = score
        if best_candidate is not None and (max_nodes is None or len(subgraph_set) < max_nodes):
            subgraph_set.add(best_candidate)
            best_score = best_candidate_score
            changed = True
        else:
            best_removal: int | None = None
            best_removal_score = best_score
            cut_vertices = _articulation_points(subgraph_set, neighbor_map)
            for node in sorted(subgraph_set):
                if node in anchors_int or node in cut_vertices:
                    continue
                trial = subgraph_set - {node}
                if not trial:
                    continue
                score = relevance.score(query_item, np.array(sorted(trial), dtype=np.int64))
                if score > best_removal_score + 1e-12:
                    best_removal = node
                    best_removal_score = score
            if best_removal is not None:
                subgraph_set.discard(best_removal)
                best_score = best_removal_score
                changed = True
        if not changed:
            break
        if best_candidate is not None:
            neighbor_map[best_candidate] = _neighbor_rows(adj, {best_candidate})[best_candidate]
    return subgraph_set


def batch(
    adj: sp.csr_matrix,
    anchor_sets: list[list[int]],
    queries: list[int],
    features: dict[str, np.ndarray],
    mask: np.ndarray,
    *,
    iters: int = 10,
    fallback: str = "anchors",
) -> list[set[int]]:
    """Run MAGE for a batch of queries and anchor sets."""
    return [
        expand(adj, anchors, query, features, mask, iters=iters, fallback=fallback)
        for anchors, query in zip(anchor_sets, queries, strict=True)
    ]


__all__ = ["batch", "expand"]
