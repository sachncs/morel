"""Item-item co-occurrence graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import scipy.sparse as sp

from morel.core.types import Array
from morel.graph import invariants
from morel.graph.bipartite import Bipartite


@dataclass(frozen=True)
class Item:
    """Symmetric item-item co-occurrence graph.

    Invariants enforced on construction:
        - no self-loops
        - symmetric (binary co-occurrence)
        - finite values

    Attributes:
        matrix: Sparse CSR adjacency matrix.
    """

    matrix: sp.csr_matrix

    def __post_init__(self) -> None:
        """Enforce graph invariants on construction."""
        if not sp.issparse(self.matrix):
            raise ValueError("item matrix must be sparse")
        matrix = self.matrix.tocsr(copy=True)
        if matrix.ndim != 2:
            raise ValueError("item matrix must be 2-D")
        if not np.issubdtype(matrix.data.dtype, np.number) or not np.isfinite(matrix.data).all():
            raise ValueError("item matrix must contain finite numeric values")
        invariants.loopless(matrix)
        invariants.symmetric(matrix)
        invariants.finite(matrix)
        matrix.sum_duplicates()
        matrix.sort_indices()
        for values in (matrix.data, matrix.indices, matrix.indptr):
            values.setflags(write=False)
        object.__setattr__(self, "matrix", matrix)

    @classmethod
    def bip(cls, bipartite: Bipartite) -> Item:
        """Construct the item-item graph from a bipartite user-item graph."""
        cooc = bipartite.matrix.T @ bipartite.matrix
        cooc = cooc.sign()
        cooc.setdiag(0)
        cooc.eliminate_zeros()
        return cls(matrix=cooc.tocsr())

    @property
    def items(self) -> int:
        """Return the number of items."""
        return int(self.matrix.shape[0])

    @property
    def edges(self) -> int:
        """Return the number of edges."""
        return int(self.matrix.nnz)

    def adjacency(self) -> sp.csr_matrix:
        """Return a writable copy of the sparse adjacency."""
        return self.matrix.copy()

    def neighbors(self, item: int) -> Array:
        """Return the sorted list of item indices connected to ``item``."""
        if not isinstance(item, (int, np.integer)) or not 0 <= item < self.items:
            raise ValueError(f"item index must be in [0, {self.items})")
        row_start = self.matrix.indptr[item]
        row_end = self.matrix.indptr[item + 1]
        return np.sort(self.matrix.indices[row_start:row_end])

    def __getstate__(self) -> dict[str, Any]:
        """Pickle support."""
        return {
            "data": self.matrix.data,
            "indices": self.matrix.indices,
            "indptr": self.matrix.indptr,
            "shape": self.matrix.shape,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Pickle support."""
        object.__setattr__(
            self,
            "matrix",
            sp.csr_matrix(
                (state["data"], state["indices"], state["indptr"]),
                shape=state["shape"],
            ),
        )
        self.__post_init__()


__all__ = ["Item"]
