"""Tests for morel.graph.bipartite and morel.graph.item."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from morel.core.errors import Net
from morel.graph import Bipartite, Item, connected, invariants


class Checker:
    """Aggregated test methods for this module."""

    def constructs(self) -> None:
        g = Bipartite(sp.csr_matrix(np.eye(2, dtype=np.float32)))
        assert g.users == 2
        assert g.items == 2
        assert g.edges == 2

    def loops(self) -> None:
        bi = Bipartite(sp.csr_matrix(np.array([[1, 1], [1, 1]], dtype=np.float32)))
        item = Item.bip(bi)
        assert (item.matrix.diagonal() == 0).all()

    def symmetric(self) -> None:
        bi = Bipartite(sp.csr_matrix(np.array([[1, 1, 0], [1, 0, 1], [0, 1, 1]], dtype=np.float32)))
        item = Item.bip(bi)
        assert (item.matrix - item.matrix.T).max() == 0

    def self(self) -> None:
        from morel.core.errors import Net

        g = sp.csr_matrix(np.eye(3, dtype=np.float32))
        with pytest.raises(Net):
            Item(matrix=g)

    def connected(self) -> None:
        nodes = np.array([0, 1, 2])
        parent = {0: np.array([1]), 1: np.array([0, 2]), 2: np.array([1])}
        assert connected(nodes, parent)

    def disconnected(self) -> None:
        nodes = np.array([0, 2])
        parent = {0: np.array([1]), 1: np.array([0, 2]), 2: np.array([1])}
        assert not connected(nodes, parent)

    def ownership(self) -> None:
        """Graph value objects isolate and protect their sparse inputs."""
        source = sp.csr_matrix(np.array([[1, 0], [0, 1]], dtype=np.float32))
        graph = Bipartite(source)
        source[0, 0] = 2
        assert graph.edges == 2
        copy = graph.adjacency()
        copy[0, 0] = 2
        assert graph.edges == 2

        item_source = sp.csr_matrix(np.array([[0, 1], [1, 0]], dtype=np.float32))
        item = Item(item_source)
        item_source[0, 1] = 0
        assert item.edges == 2
        item_copy = item.adjacency()
        item_copy[0, 1] = 0
        assert item.edges == 2

    def empty(self) -> None:
        """Zero-item and isolated graphs remain valid value objects."""
        zero_items = Item.bip(Bipartite(sp.csr_matrix((3, 0), dtype=np.float32)))
        assert zero_items.items == 0
        assert zero_items.edges == 0

        isolated = Item.bip(Bipartite(sp.csr_matrix((2, 3), dtype=np.float32)))
        assert isolated.items == 3
        assert isolated.edges == 0

    def duplicate_edges(self) -> None:
        """Duplicate sparse entries are canonicalized before graph derivation."""
        source = sp.coo_matrix(([1.0, 1.0], ([0, 0], [1, 1])), shape=(1, 2))
        item = Item.bip(Bipartite(source))
        assert item.edges == 0

    def self_loops_are_removed(self) -> None:
        """Co-occurrence self-loops are removed during item graph construction."""
        source = sp.csr_matrix(np.eye(3, dtype=np.float32))
        item = Item.bip(Bipartite(source))
        assert item.edges == 0

    def malformed_item_input_is_rejected(self) -> None:
        """Dense and non-numeric item inputs fail at the value-object boundary."""
        with pytest.raises(ValueError, match="must be sparse"):
            Item(np.zeros((2, 2), dtype=np.float32))  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="finite numeric"):
            Item(sp.csr_matrix(np.array([[0.0, np.nan], [np.nan, 0.0]])))

    def neighbors_bounds_are_explicit(self) -> None:
        """Neighbor lookup rejects indices outside the item graph."""
        item = Item(sp.csr_matrix(np.zeros((2, 2), dtype=np.float32)))
        with pytest.raises(ValueError, match="item index must be in"):
            item.neighbors(-1)
        with pytest.raises(ValueError, match="item index must be in"):
            item.neighbors(2)

    def invariant_boundaries(self) -> None:
        """Graph invariants reject malformed shapes and controls with Net."""
        with pytest.raises(Net, match="sparse"):
            invariants.symmetric(np.eye(2))  # type: ignore[arg-type]
        with pytest.raises(Net, match="square"):
            invariants.symmetric(sp.csr_matrix(np.zeros((2, 3))))
        with pytest.raises(Net, match="minimum degree"):
            invariants.isoless(sp.csr_matrix(np.zeros((2, 2))), min_degree=-1)
        with pytest.raises(Net, match="tolerance"):
            invariants.symmetric(sp.eye(2), atol=-1)

    def invariant_values(self) -> None:
        """Non-numeric and non-finite graph values stay inside Net."""
        with pytest.raises(Net, match="numeric"):
            invariants.finite(np.asarray([["x"]], dtype=object))  # type: ignore[arg-type]
        with pytest.raises(Net, match="non-finite"):
            invariants.finite(sp.csr_matrix(np.array([[np.nan]], dtype=np.float32)))
