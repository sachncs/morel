"""Modality-availability relevance and mean relevance.

The relevance score r(i, v) is the arithmetic mean of cosine similarities over
modalities jointly observed for both nodes i and v.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from morel.core.errors import Shape
from morel.core.types import Array


def scale(matrix: Array) -> tuple[Array, Array]:
    """Row-normalize ``matrix`` and return ``(normalized, valid_mask)``.

    Rows with zero norm are kept as zero vectors; the returned mask marks
    them as invalid.
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe = np.where(norms == 0.0, 1.0, norms)
    return matrix / safe, (norms.flatten() > 0)


@dataclass(frozen=True)
class RelevanceIndex:
    """Pre-normalized feature state for repeated relevance queries.

    MAGE evaluates many add/remove candidates for one query. Keeping the
    normalized modality matrices in this immutable value avoids rescanning
    and normalizing the entire catalog for every candidate.
    """

    normalized: dict[str, Array]
    valid: dict[str, Array]
    mask: Array
    _query_scores: dict[int, Array] = field(default_factory=dict, repr=False, compare=False)
    _query_usable: dict[int, Array] = field(default_factory=dict, repr=False, compare=False)

    def _scores_for_query(self, i: int) -> Array:
        """Return cached relevance from query ``i`` to every catalog item."""
        cached = self._query_scores.get(int(i))
        if cached is not None:
            return cached
        scores = np.zeros(self.mask.shape[0], dtype=np.float64)
        denominators = np.zeros(self.mask.shape[0], dtype=np.float64)
        for mod_idx, name in enumerate(self.normalized):
            normalized = self.normalized[name]
            valid = self.valid[name]
            if not valid[i] or self.mask[i, mod_idx] <= 0:
                continue
            available = (self.mask[:, mod_idx] > 0) & valid
            if not available.any():
                continue
            scores[available] += normalized[available] @ normalized[i]
            denominators[available] += 1.0
        result = np.divide(
            scores,
            denominators,
            out=np.zeros_like(scores),
            where=denominators > 0,
        )
        self._query_scores[int(i)] = result
        self._query_usable[int(i)] = denominators > 0
        return result

    def score(self, i: int, nodes: Array) -> float:
        """Return mean relevance for ``i`` over ``nodes``."""
        if nodes.size == 0:
            return 0.0
        candidates = np.asarray(nodes, dtype=np.int64)
        candidates = candidates[candidates != i]
        if candidates.size == 0:
            return 0.0
        values = self._scores_for_query(int(i))[candidates]
        usable = self._query_usable[int(i)][candidates]
        return float(values[usable].mean()) if usable.any() else 0.0


def prepare(features: dict[str, Array], mask: Array) -> RelevanceIndex:
    """Build reusable normalized state for repeated relevance calculations."""
    if not features:
        raise Shape("features dict is empty")
    if mask.ndim != 2 or mask.shape[1] != len(features):
        raise Shape(f"mask shape {mask.shape} incompatible with {len(features)} modalities")
    normalized: dict[str, Array] = {}
    valid: dict[str, Array] = {}
    for name, values in features.items():
        values_normalized, values_valid = scale(values.astype(np.float64, copy=False))
        normalized[name] = values_normalized
        valid[name] = values_valid
    return RelevanceIndex(normalized=normalized, valid=valid, mask=mask)


def relevance(
    i: int,
    v: int,
    features: dict[str, Array],
    mask: Array,
) -> float:
    """Cosine relevance r(i, v) over jointly observed modalities.

    Args:
    i : int
        Query node id.
    v : int
        Candidate node id.
    features : dict[str, Array]
        Dict mapping modality name to ``(items, dim)`` float32 arrays.
    mask : Array
        Binary availability mask of shape ``(items, modalities)``.

    Returns:
    float
        Mean cosine similarity in ``[0, 1]``. Returns 0.0 when no modality is
        jointly observed.
    """
    if not features:
        raise Shape("features dict is empty")
    if mask.ndim != 2:
        raise Shape(f"mask must be 2-D, got {mask.ndim}-D")
    modalities = list(features.keys())
    numerator = 0.0
    denominator = 0.0
    for mod_idx, name in enumerate(modalities):
        if mask[i, mod_idx] <= 0 or mask[v, mod_idx] <= 0:
            continue
        vec_i = features[name][i].astype(np.float64, copy=False)
        vec_v = features[name][v].astype(np.float64, copy=False)
        norm_i = float(np.linalg.norm(vec_i))
        norm_v = float(np.linalg.norm(vec_v))
        if norm_i <= 0 or norm_v <= 0:
            continue
        numerator += float(np.dot(vec_i, vec_v) / (norm_i * norm_v))
        denominator += 1.0
    if denominator == 0:
        return 0.0
    return numerator / denominator


def rel(
    i: int,
    nodes: Array,
    features: dict[str, Array],
    mask: Array,
) -> float:
    """Mean of r(i, v) over ``nodes``, excluding the query.

    Vectorised: pre-normalises each modality's features once, then for
    each candidate computes the cosine similarity in one matmul and
    averages over jointly observed modalities.

    Args:
    i : int
        Query node id.
    nodes : Array
        Candidate node ids (1-D).
    features : dict[str, Array]
        Dict of feature arrays.
    mask : Array
        Modality availability mask.

    Returns:
    float
        Mean relevance. Returns 0.0 if no candidates.
    """
    return prepare(features, mask).score(i, nodes)


__all__ = ["RelevanceIndex", "prepare", "rel", "relevance", "scale"]
