"""Recommender Protocol.

Defines the contract that any downstream ranker must satisfy so the
``Recommendation`` trainer and the serve stack can consume them
uniformly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import scipy.sparse as sp
import torch


@runtime_checkable
class Recommender(Protocol):
    """One downstream ranker.

    Implementations accept a batch of user ids, a batch of item ids, and
    optionally a bipartite ``ui_graph`` whose normalized adjacency they
    may rebuild. They return a ``(B_u, B_i)`` score matrix.

    Attributes:
        forward: Returns user-item score matrix.
    """

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


__all__ = ["FeatureAware", "Fits", "Normalizes", "Recommender"]
