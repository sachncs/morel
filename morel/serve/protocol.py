"""Runtime contract for pipelines mounted in the inference service."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import scipy.sparse as sp
import torch

from morel.core.types import Array


class CompletionOutput(Protocol):
    """Minimum output shape required by the completion endpoint."""

    completed: dict[str, torch.Tensor]


@runtime_checkable
class ServingPipeline(Protocol):
    """Minimum structural contract required by the HTTP serving layer."""

    cfeat: dict[str, Array] | None
    cmask: Array | None
    cadj: sp.csr_matrix | None
    ui_graph: sp.csr_matrix | None
    recommender: object | None
    user_count: int
    item_count: int

    def __call__(self, *args: Any, **kwargs: Any) -> CompletionOutput:
        """Complete a batch of item features."""

    def score(self, users: torch.Tensor, items: torch.Tensor) -> torch.Tensor:
        """Score explicit user and item id batches."""


def is_serving_pipeline(value: object) -> bool:
    """Return whether ``value`` satisfies the runtime serving contract."""
    return isinstance(value, ServingPipeline)


__all__ = ["CompletionOutput", "ServingPipeline", "is_serving_pipeline"]
