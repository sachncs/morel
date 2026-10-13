"""Streaming ingestion primitives.

Two-pass exact k-core via stream: pass 1 collects degree counts, pass 2
emits the filtered edges. Online degree-filter uses a rolling window for
the IterableDataset training path.
"""

from __future__ import annotations

import json
from collections import Counter, deque
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp

from morel.core.errors import Datum


def _positive_int(value: int, name: str) -> None:
    """Validate a positive streaming parameter."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise Datum(f"{name} must be a positive integer, got {value!r}")


def _pair(record: object) -> tuple[str, str] | None:
    """Extract a valid Amazon user/item pair from one decoded record."""
    if not isinstance(record, dict):
        return None
    user = record.get("reviewerID")
    item = record.get("asin")
    if not isinstance(user, str) or not user.strip():
        return None
    if not isinstance(item, str) or not item.strip():
        return None
    return user, item


def review(path: Path | str, *, chunk_size: int = 100_000) -> Iterator[list[dict[str, Any]]]:
    """Yield chunks of JSON-decoded records from an Amazon review file.

    Args
    ----
    path : Path | str
        Path to the decompressed ``.json`` file (one JSON object per line).
    chunk_size : int
        Maximum number of records per chunk.

    Yields
    ------
    list[dict]
        A list of at most ``chunk_size`` parsed records.
    """
    _positive_int(chunk_size, "chunk_size")
    target = Path(path)
    if not target.exists():
        raise Datum(f"review file not found: {target}")
    chunk: list[dict[str, Any]] = []
    try:
        with target.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                chunk.append(record)
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk
    except (OSError, UnicodeError) as exc:
        raise Datum(f"unable to read review file: {target}") from exc


def stream(
    review_path: Path | str,
    *,
    min_edges: int = 5,
    chunk_size: int = 100_000,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield ``(user_ids_chunk, item_ids_chunk)`` for an Amazon review file.

    Args
    ----
    review_path : Path | str
        Path to the decompressed ``.json`` file.
    min_edges : int
        Nodes whose rolling-window degree is below this are filtered out
        (online degree filter).
    chunk_size : int
        Records per streaming chunk.

    Yields
    ------
    tuple[np.ndarray, np.ndarray]
        ``(user_ids, item_ids)`` for each chunk after filtering.
    """
    _positive_int(min_edges, "min_edges")
    _positive_int(chunk_size, "chunk_size")
    rolling_window: deque[tuple[str, str]] = deque(maxlen=chunk_size * 4)
    degree_counter: Counter[str] = Counter()
    seen_pairs: set[tuple[str, str]] = set()

    for chunk in review(review_path, chunk_size=chunk_size):
        for record in chunk:
            pair = _pair(record)
            if pair is None:
                continue
            user, item = pair
            key = (user, item)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            # Increment first, then check the threshold; this matches the
            # offline k-core filter semantics.
            degree_counter[user] += 1
            degree_counter[item] += 1
            if degree_counter[user] >= min_edges and degree_counter[item] >= min_edges:
                rolling_window.append(key)
        if rolling_window:
            users = np.array([u for u, _ in rolling_window])
            items = np.array([i for _, i in rolling_window])
            yield users, items


def confirmed(
    review_path: Path | str,
    *,
    min_edges: int = 5,
    chunk_size: int = 100_000,
) -> tuple[sp.csr_matrix, dict[str, int], dict[str, int]]:
    """Two-pass exact k-core streaming loader.

    Pass 1 accumulates degree counts; pass 2 emits only edges whose
    endpoints satisfy the degree threshold. Output is bit-identical to
    the in-memory :func:`morel.data.build.interactions` on the same input.

    Args
    ----
    review_path : Path | str
        Path to the decompressed ``.json`` file.
    min_edges : int
        Minimum degree per node.
    chunk_size : int
        Records per streaming chunk.

    Returns
    -------
    tuple[sp.csr_matrix, dict[str, int], dict[str, int]]
        ``(ui_graph, user_id_to_idx, item_id_to_idx)``.
    """
    _positive_int(min_edges, "min_edges")
    _positive_int(chunk_size, "chunk_size")
    review_path = Path(review_path)
    if not review_path.exists():
        raise Datum(f"review file not found: {review_path}")

    user_counts: Counter[str] = Counter()
    item_counts: Counter[str] = Counter()
    counted: set[tuple[str, str]] = set()
    for chunk in review(review_path, chunk_size=chunk_size):
        for record in chunk:
            pair = _pair(record)
            if pair is None:
                continue
            user, item = pair
            if pair in counted:
                continue
            counted.add(pair)
            user_counts[user] += 1
            item_counts[item] += 1

    keep_users = {u for u, c in user_counts.items() if c >= min_edges}
    keep_items = {i for i, c in item_counts.items() if c >= min_edges}

    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for chunk in review(review_path, chunk_size=chunk_size):
        for record in chunk:
            pair = _pair(record)
            if pair is None:
                continue
            user, item = pair
            if user not in keep_users or item not in keep_items:
                continue
            key = (user, item)
            if key in seen:
                continue
            seen.add(key)
            pairs.append(key)

    if not pairs:
        raise Datum("k-core filtering produced empty interaction set")

    users = sorted({u for u, _ in pairs})
    items = sorted({i for _, i in pairs})
    user2id = {u: idx for idx, u in enumerate(users)}
    item2id = {i: idx for idx, i in enumerate(items)}
    u_arr = np.array([user2id[u] for u, _ in pairs], dtype=np.int64)
    i_arr = np.array([item2id[i] for _, i in pairs], dtype=np.int64)
    # Build the bipartite directly to avoid an import cycle through
    # morel.data.build (which itself imports confirmed for its
    # in-memory interactions() path).
    data = np.ones(u_arr.shape[0], dtype=np.float32)
    ui = sp.csr_matrix((data, (u_arr, i_arr)), shape=(len(users), len(items)))
    ui.sum_duplicates()
    return ui, user2id, item2id


def cooc(
    ui_chunks: Iterator[tuple[np.ndarray, np.ndarray]],
    *,
    items: int,
) -> sp.csr_matrix:
    """Build an item co-occurrence graph from a stream of bipartite chunks.

    Memory scales with the number of user-item edges actually seen,
    not with the pair count. For each user, the items they touched
    form a clique; we walk the per-user item set and emit an
    (a, b, count) triple into a sparse ``coo_matrix`` accumulator.

    Args
    ----
    ui_chunks : Iterator
        Stream of ``(user_ids, item_ids)`` pairs.
    items : int
        Number of items.

    Returns
    -------
    sp.csr_matrix
        Symmetric ``(items, items)`` item co-occurrence adjacency.
    """
    _positive_int(items, "items")
    rows: list[int] = []
    cols: list[int] = []
    data: list[int] = []
    for user_ids, item_ids in ui_chunks:
        users_array = np.asarray(user_ids)
        items_array = np.asarray(item_ids)
        if users_array.ndim != 1 or items_array.ndim != 1:
            raise Datum("stream chunks must contain one-dimensional id arrays")
        if users_array.shape != items_array.shape:
            raise Datum("stream user and item chunks must have equal lengths")
        if items_array.size and not np.issubdtype(items_array.dtype, np.integer):
            raise Datum("stream item ids must be integers")
        if items_array.size and (np.any(items_array < 0) or np.any(items_array >= items)):
            raise Datum("stream item id is outside the catalog bounds")
        per_user_items = sorted({int(i) for i in items_array})
        for idx, a in enumerate(per_user_items):
            for b in per_user_items[idx + 1 :]:
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
    "confirmed",
    "cooc",
    "review",
    "stream",
]
