"""Runtime contract for pipelines mounted in the inference service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

import numpy as np
import scipy.sparse as sp


@runtime_checkable
class ServingPipeline(Protocol):
    """Minimum structural contract required by the HTTP serving layer."""

    cfeat: dict[str, np.ndarray] | None
    cmask: np.ndarray | None
    cadj: sp.csr_matrix | None
    ui_graph: sp.csr_matrix | None
    recommender: Callable[..., Any] | None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Complete a batch of item features."""


def is_serving_pipeline(value: object) -> bool:
    """Return whether ``value`` satisfies the runtime serving contract."""
    return isinstance(value, ServingPipeline)


__all__ = ["ServingPipeline", "is_serving_pipeline"]
