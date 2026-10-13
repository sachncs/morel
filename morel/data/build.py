"""Graph construction: bipartite user-item and item-item co-occurrence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp

from morel.core.errors import Datum
from morel.core.log import get as logger
from morel.data.stream import MAX_COO_EDGES, confirmed

log = logger("data.build")


def bipartite(user: np.ndarray, item: np.ndarray, users: int, items: int) -> sp.csr_matrix:
    """Build a user-item bipartite adjacency matrix.

    Args:
        user: 1-D array of user indices.
        item: 1-D array of item indices, same length as ``user``.
        users: Total number of users.
        items: Total number of items.

    Returns
    -------
        Sparse CSR matrix of shape ``(users, items)`` with float32 ones.
    """
    if user.ndim != 1 or item.ndim != 1:
        raise Datum("user and item ids must be 1-D arrays")
    if user.shape != item.shape:
        raise Datum(f"shape mismatch: user {user.shape} vs item {item.shape}")
    if users <= 0 or items <= 0:
        raise Datum(f"graph dimensions must be positive, got users={users}, items={items}")
    if not np.issubdtype(user.dtype, np.integer) or not np.issubdtype(item.dtype, np.integer):
        raise Datum("user and item ids must use integer dtypes")
    if user.size and (user.min() < 0 or user.max() >= users):
        raise Datum(f"user ids must be in [0, {users})")
    if item.size and (item.min() < 0 or item.max() >= items):
        raise Datum(f"item ids must be in [0, {items})")
    data = np.ones(user.shape[0], dtype=np.float32)
    matrix = sp.csr_matrix((data, (user, item)), shape=(users, items))
    matrix.sum_duplicates()
    return matrix


def cooccurrence(graph: sp.csr_matrix) -> sp.csr_matrix:
    """Build an item-item co-occurrence graph from a user-item bipartite.

    The result is binarized, symmetrized, and self-loops are removed.

    Args:
        graph: User-item adjacency of shape ``(users, items)``.

    Returns
    -------
        Symmetric item-item CSR matrix with no self-loops.
    """
    if graph.ndim != 2:
        raise Datum(f"bipartite must be 2-D, got {graph.ndim}-D")
    cooc = graph.T @ graph
    cooc = cooc.sign()
    cooc.setdiag(0)
    cooc.eliminate_zeros()
    return cooc.tocsr()


def kcore(graph: sp.csr_matrix, min_edges: int) -> sp.csr_matrix:
    """Peel nodes below ``min_edges`` until stable.

    Implements strict k-core: every node in the returned graph has at least
    ``min_edges`` surviving neighbors.

    Args:
        graph: Symmetric item-item CSR.
        min_edges: Minimum number of neighbors per node.

    Returns
    -------
        The largest subgraph satisfying the k-core invariant.
    """
    if min_edges <= 0:
        return graph
    current = graph.copy()
    while True:
        degrees = np.asarray(current.sum(axis=1)).flatten()
        keep = degrees >= min_edges
        if keep.all():
            return current
        keep_indices = np.where(keep)[0]
        sub = current[keep_indices][:, keep_indices]
        sub = sub.tocsr()
        sub.sum_duplicates()
        current = sub
        if current.shape[0] == 0:
            return current


def interactions(
    review: Path | str,
    metadata: Path | str | None = None,
    *,
    min_edges: int = 5,
) -> tuple[sp.csr_matrix, dict[int, dict[str, Any]], int, int]:
    """Stream Amazon reviews into a filtered bipartite graph.

    The previous implementation buffered every (user, item) pair into a
    Python list before applying k-core filtering, which used multi-GB
    of memory on the Amazon-Reviews-2023 Beauty split. The current
    implementation delegates the heavy lifting to
    :func:`morel.data.stream.confirmed` (two passes over the JSON
    file) so memory scales with the post-filter edge count rather
    than the raw review volume.

    Item metadata is loaded line-by-line; entries are dropped if the
    ``asin`` is not in the surviving item set.

    Args:
        review: Path to the Amazon reviews ``.json`` file.
        metadata: Optional path to the Amazon metadata ``.json`` file;
            ignored when missing.
        min_edges: K-core threshold.

    Returns
    -------
        Tuple of ``(ui_graph, item_meta, users, items)``.
    """
    review_path = Path(review)
    if not review_path.exists():
        raise Datum(f"review file not found: {review_path}")
    ui, user2id, item2id = confirmed(review_path, min_edges=min_edges)

    item_meta: dict[int, dict[str, Any]] = {}
    if metadata is not None and Path(metadata).exists():
        import json

        skipped_meta = 0
        with Path(metadata).open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    skipped_meta += 1
                    continue
                if not isinstance(record, dict):
                    skipped_meta += 1
                    continue
                asin = record.get("asin")
                if asin is not None and asin in item2id:
                    item_meta[item2id[asin]] = record
        if skipped_meta:
            log.warning("skipped malformed metadata lines", extra={"count": skipped_meta})
    return ui, item_meta, len(user2id), len(item2id)


def cooccurrence_stream(
    review_path: Path | str,
    *,
    items: int,
    min_edges: int = 5,
    chunk_size: int = 100_000,
    max_edges: int = MAX_COO_EDGES,
) -> sp.csr_matrix:
    """Build an item co-occurrence graph in a single streaming pass.

    The previous :func:`morel.data.stream.cooc` accumulated every
    item-pair into a Python dict, which scaled with the pair count
    (typically O(users^2) per user). This implementation accumulates
    the pairs into a sparse ``coo_matrix`` accumulator so memory
    scales with the per-chunk edge count, not the pair count.

    Args:
        review_path: Path to the decompressed ``.json`` reviews file.
        items: Number of items in the catalogue.
        min_edges: Online degree filter applied while streaming.
        chunk_size: Reviews per streaming chunk.
        max_edges: Maximum number of directed COO entries accumulated before
            failing closed.

    Returns
    -------
        Symmetric ``(items, items)`` item co-occurrence adjacency.
    """
    from morel.data.stream import stream

    if isinstance(max_edges, bool) or not isinstance(max_edges, int) or max_edges <= 0:
        raise Datum(f"max_edges must be a positive integer, got {max_edges!r}")
    rows: list[int] = []
    cols: list[int] = []
    data: list[int] = []
    for user_chunk, item_chunk in stream(review_path, min_edges=min_edges, chunk_size=chunk_size):
        # Items form a clique only within one user. Grouping here prevents
        # unrelated users in the same stream chunk from creating false edges.
        by_user: dict[str, set[int]] = {}
        for user, item in zip(user_chunk.tolist(), item_chunk.tolist(), strict=True):
            by_user.setdefault(str(user), set()).add(int(item))
        for per_user_items_set in by_user.values():
            per_user_items = sorted(per_user_items_set)
            for idx, a in enumerate(per_user_items):
                for b in per_user_items[idx + 1 :]:
                    if len(rows) + 2 > max_edges:
                        raise Datum(
                            f"co-occurrence edge budget exceeded: {max_edges} directed entries"
                        )
                    rows.append(a)
                    cols.append(b)
                    data.append(1)
                    rows.append(b)
                    cols.append(a)
                    data.append(1)
    matrix = sp.coo_matrix((data, (rows, cols)), shape=(items, items))
    matrix.setdiag(0)
    matrix.eliminate_zeros()
    return matrix.tocsr()


__all__ = [
    "bipartite",
    "cooccurrence",
    "cooccurrence_stream",
    "interactions",
    "kcore",
]
