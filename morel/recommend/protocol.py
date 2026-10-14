"""Recommender Protocol.

Defines the contract that any downstream ranker must satisfy so the
``Recommendation`` trainer and the serve stack can consume them
uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import scipy.sparse as sp
import torch


@dataclass(frozen=True)
class RecommenderCapabilities:
    """Declared optional behavior exposed by one recommender implementation."""

    item_features: bool
    normalizes: bool
    fits: bool


@runtime_checkable
class Recommender(Protocol):
    """One downstream ranker.

    Implementations accept a batch of user ids, a batch of item ids, and
    optionally a bipartite ``ui_graph`` whose normalized adjacency they
    may rebuild. They return a ``(B_u, B_i)`` score matrix.

    Attributes:
        forward: Returns user-item score matrix.
        capabilities: Explicit optional behavior supported by this ranker.
    """

    capabilities: RecommenderCapabilities

    def forward(
        self,
        users: torch.Tensor,
        items: torch.Tensor,
        ui_graph: sp.csr_matrix | None = None,
    ) -> torch.Tensor:  # pragma: no cover - protocol
        """Score the (users, items) batch into a ``(B_u, B_i)`` matrix."""
        ...


@runtime_checkable
class FeatureAware(Protocol):
    """Optional capability for rankers that consume completed item features."""

    def score_with_features(
        self,
        users: torch.Tensor,
        items: torch.Tensor,
        ui_graph: sp.csr_matrix | None,
        item_features: torch.Tensor,
    ) -> torch.Tensor:
        """Score items after incorporating completed modality features."""
        ...


@runtime_checkable
class Normalizes(Protocol):
    """Optional capability for graph recommenders with cached normalization."""

    def normalize(self, ui_graph: sp.csr_matrix) -> torch.Tensor:
        """Prepare or retrieve normalized graph state."""
        ...


@runtime_checkable
class Fits(Protocol):
    """Optional capability for recommenders requiring corpus fitting."""

    def fit(self, ui_graph: sp.csr_matrix) -> None:
        """Fit graph-derived item state."""
        ...


def declared_capabilities(value: object) -> RecommenderCapabilities | None:
    """Return validated recommender capabilities or ``None``.

    Keeping this check beside the protocols prevents registries and pipeline
    composition from making subtly different assumptions about optional
    recommender behavior.
    """
    if not isinstance(value, Recommender):
        return None
    try:
        capabilities = value.capabilities
    except Exception:
        return None
    if not isinstance(capabilities, RecommenderCapabilities):
        return None
    if capabilities.item_features != isinstance(value, FeatureAware):
        return None
    if capabilities.normalizes != isinstance(value, Normalizes):
        return None
    if capabilities.fits != isinstance(value, Fits):
        return None
    return capabilities


__all__ = [
    "FeatureAware",
    "Fits",
    "Normalizes",
    "Recommender",
    "RecommenderCapabilities",
    "declared_capabilities",
]
