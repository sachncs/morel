"""Graph invariants asserted at construction time."""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from morel.core.errors import Net


def _require_square(adj: sp.spmatrix) -> None:
    """Validate the sparse square-matrix contract shared by invariants."""
    if not sp.issparse(adj):
        raise Net("graph must be sparse")
    if adj.ndim != 2 or adj.shape[0] != adj.shape[1]:
        raise Net(f"graph must be square, got {getattr(adj, 'shape', None)}")


def loopless(adj: sp.spmatrix) -> None:
    """Raise if the adjacency has any self-loops."""
    _require_square(adj)
    finite(adj)
    diag = adj.diagonal()
    if (diag != 0).any():
        raise Net("graph has self-loops")


def symmetric(adj: sp.spmatrix, *, atol: float = 1e-6) -> None:
    """Raise if the adjacency is not symmetric up to ``atol``."""
    _require_square(adj)
    finite(adj)
    if not np.isfinite(atol) or atol < 0:
        raise Net("graph symmetry tolerance must be finite and non-negative")
    diff = adj - adj.T
    if isinstance(diff, sp.spmatrix):
        diff = diff.tocsr()
        if diff.nnz == 0:
            return
    elif np.size(diff) == 0:
        return
    if abs(diff).max() > atol:
        raise Net("graph is not symmetric")


def isoless(adj: sp.spmatrix, *, min_degree: int = 1) -> None:
    """Raise if any node has degree below ``min_degree``."""
    _require_square(adj)
    finite(adj)
    if not isinstance(min_degree, (int, np.integer)) or min_degree < 0:
        raise Net("minimum degree must be a non-negative integer")
    degrees = np.asarray(adj.sum(axis=1)).flatten()
    if (degrees < min_degree).any():
        raise Net("graph has isolated nodes")


def finite(adj: sp.spmatrix) -> None:
    """Raise if the adjacency contains non-finite values."""
    try:
        values = adj.data if sp.issparse(adj) else np.asarray(adj)
        if not np.isfinite(values).all():
            raise Net("graph contains non-finite values")
    except TypeError as exc:
        raise Net("graph values must be numeric") from exc


def verify_all(adj: sp.spmatrix) -> None:
    """Run the full default invariant suite."""
    finite(adj)
    loopless(adj)
    symmetric(adj)
    isoless(adj)


__all__ = ["finite", "isoless", "loopless", "symmetric", "verify_all"]
