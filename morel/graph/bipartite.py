"""Bipartite user-item graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import scipy.sparse as sp

from morel.core.types import Array


@dataclass(frozen=True)
class Bipartite:
    """Immutable user-item bipartite graph.

    Attributes:
        matrix: Sparse CSR adjacency matrix.
    """

    matrix: sp.csr_matrix

    def __post_init__(self) -> None:
        """Validate that the matrix is 2-D and sparse."""
        if not sp.issparse(self.matrix):
            raise ValueError("bipartite matrix must be sparse")
        matrix = self.matrix.tocsr(copy=True)
        if matrix.ndim != 2:
            raise ValueError("bipartite matrix must be 2-D")
        if not np.issubdtype(matrix.data.dtype, np.number) or not np.isfinite(matrix.data).all():
            raise ValueError("bipartite matrix must contain finite numeric values")
        matrix.sum_duplicates()
        matrix.sort_indices()
        for values in (matrix.data, matrix.indices, matrix.indptr):
            values.setflags(write=False)
        object.__setattr__(self, "matrix", matrix)

    @property
    def users(self) -> int:
        """Return the number of users."""
        return int(self.matrix.shape[0])

    @property
    def items(self) -> int:
        """Return the number of items."""
        return int(self.matrix.shape[1])

    @property
    def edges(self) -> int:
        """Return the number of nonzero entries."""
        return int(self.matrix.nnz)

    def adjacency(self) -> sp.csr_matrix:
        """Return a writable copy of the sparse adjacency."""
        return self.matrix.copy()

    def dense(self) -> Array:
        """Return a dense copy as a numpy array."""
        dense: Array = self.matrix.toarray()
        return dense

    def __getstate__(self) -> dict[str, Any]:
        """Pickle support: return CSR arrays."""
        return {
            "data": self.matrix.data,
            "indices": self.matrix.indices,
            "indptr": self.matrix.indptr,
            "shape": self.matrix.shape,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Pickle support: rebuild from CSR arrays."""
        object.__setattr__(
            self,
            "matrix",
            sp.csr_matrix(
                (state["data"], state["indices"], state["indptr"]),
                shape=state["shape"],
            ),
        )
        self.__post_init__()


__all__ = ["Bipartite"]
