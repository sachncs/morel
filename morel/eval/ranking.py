"""Vectorized ranking metrics."""

from __future__ import annotations

import numpy as np

from morel.core.types import Array


def _top_k(scores: Array, k: int) -> tuple[Array, int]:
    """Return top-k indices and the effective cutoff for a score matrix."""
    if scores.ndim != 2:
        raise ValueError(f"scores must be 2-D, got {scores.ndim}-D")
    width = scores.shape[1]
    if width == 0:
        return np.empty((scores.shape[0], 0), dtype=np.int64), 0
    effective = min(k, width)
    indices = np.argpartition(-scores, kth=effective - 1, axis=1)[:, :effective]
    return indices, effective


def recall(scores: Array, labels: Array, *, k: int = 10) -> float:
    """Mean Recall@K across users with at least one relevant item.

    Args:
        scores: ``(users, items)`` predicted scores.
        labels: ``(users, items)`` binary relevance.
        k: Cutoff.

    Returns:
        Scalar Recall@K in ``[0, 1]``.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    if scores.shape != labels.shape:
        raise ValueError(f"score/label shape mismatch: {scores.shape} vs {labels.shape}")
    top_k, effective = _top_k(scores, k)
    if effective == 0:
        return 0.0
    relevant = labels.sum(axis=1)
    mask = relevant > 0
    if not mask.any():
        return 0.0
    hits = np.take_along_axis(labels, top_k, axis=1).sum(axis=1)
    return float((hits[mask] / relevant[mask]).mean())


def ndcg(scores: Array, labels: Array, *, k: int = 10) -> float:
    """Mean NDCG@K.

    Args:
        scores: ``(users, items)`` predicted scores.
        labels: ``(users, items)`` binary relevance.
        k: Cutoff.

    Returns:
        Scalar NDCG@K in ``[0, 1]``.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    if scores.shape != labels.shape:
        raise ValueError(f"score/label shape mismatch: {scores.shape} vs {labels.shape}")
    top_k, effective = _top_k(scores, k)
    if effective == 0:
        return 0.0
    relevances = np.take_along_axis(labels, top_k, axis=1)
    positions = np.arange(1, effective + 1)
    discounts = 1.0 / np.log2(positions + 1)
    dcg = (relevances * discounts).sum(axis=1)
    ideal = np.sort(labels, axis=1)[:, ::-1][:, :k]
    idcg = (ideal * discounts).sum(axis=1)
    valid = idcg > 0
    if not valid.any():
        return 0.0
    return float((dcg[valid] / idcg[valid]).mean())


def precision(scores: Array, labels: Array, *, k: int = 10) -> float:
    """Mean Precision@K."""
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    top_k, effective = _top_k(scores, k)
    if effective == 0:
        return 0.0
    hits = np.take_along_axis(labels, top_k, axis=1).sum(axis=1)
    return float((hits / effective).mean())


def mrr(scores: Array, labels: Array) -> float:
    """Mean reciprocal rank of the first relevant item.

    Uses ``argpartition`` to find the position of the highest-scoring
    relevant item in expected O(N) instead of sorting the full row in
    O(N log N).
    """
    has_relevant = labels.sum(axis=1) > 0
    if not has_relevant.any():
        return 0.0
    # Mask non-relevant items and find each row's highest-scoring relevant
    # item directly. This avoids sorting the full catalog per user.
    masked_scores = np.where(labels > 0, scores, -np.inf)
    best_relevant = np.argmax(masked_scores, axis=1)
    best_scores = np.take_along_axis(scores, best_relevant[:, None], axis=1)
    ranks = (scores > best_scores).sum(axis=1)
    rr = 1.0 / (ranks[has_relevant] + 1)
    return float(rr.mean())


def map(scores: Array, labels: Array, *, k: int = 10) -> float:
    """Mean Average Precision@K."""
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    top_k, effective = _top_k(scores, k)
    if effective == 0:
        return 0.0
    relevances = np.take_along_axis(labels, top_k, axis=1)
    cumulative = np.cumsum(relevances > 0, axis=1)
    positions = np.arange(1, effective + 1)
    precision_at_i = cumulative / positions
    average = (precision_at_i * relevances).sum(axis=1)
    relevant = labels.sum(axis=1).clip(min=1)
    return float((average / relevant).mean())


__all__ = ["map", "mrr", "ndcg", "precision", "recall"]
