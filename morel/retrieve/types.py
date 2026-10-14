"""Type aliases for the retrieval module."""

from __future__ import annotations

from collections.abc import Callable

import scipy.sparse as sp

from morel.core.types import Array

Strategy = Callable[
    [int, dict[str, Array], Array, sp.csr_matrix],
    set[int],
]

StrategyFn = Callable[
    [
        int,
        dict[str, Array],
        Array,
        sp.csr_matrix,
    ],
    set[int],
]

__all__ = ["Strategy", "StrategyFn"]
