"""Tests for morel.retrieve.mage."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from morel.core.errors import Net
from morel.retrieve.bfs import neighbors_map
from morel.retrieve.mage import _articulation_points, expand


@pytest.fixture
def setup() -> tuple[dict[str, np.ndarray], np.ndarray, sp.csr_matrix]:
    g = sp.csr_matrix(
        np.array(
            [[0, 1, 0, 0, 0], [1, 0, 1, 0, 0], [0, 1, 0, 1, 0], [0, 0, 1, 0, 1], [0, 0, 0, 1, 0]],
            dtype=np.float32,
        )
    )
    features = {"visual": np.eye(5, dtype=np.float32), "text": np.eye(5, dtype=np.float32)}
    mask = np.ones((5, 2), dtype=np.float32)
    return features, mask, g


class Checker:
    """Aggregated test methods for this module."""

    def query(self, setup) -> None:
        features, mask, g = setup
        sub = expand(g, [1, 3], 0, features, mask, iters=3)
        assert 0 in sub

    def anchors(self, setup) -> None:
        features, mask, g = setup
        sub = expand(g, [1, 3], 0, features, mask, iters=5)
        # The query (0) is added; if best-improvement never triggers removal
        # of anchors, they stay. We only assert the query is included.
        assert 0 in sub

    def deterministic(self, setup) -> None:
        features, mask, g = setup
        a = expand(g, [1, 3], 0, features, mask, iters=5)
        b = expand(g, [1, 3], 0, features, mask, iters=5)
        assert a == b

    def iters(self, setup) -> None:
        features, mask, g = setup
        with pytest.raises(Net):
            expand(g, [1, 3], 0, features, mask, iters=0)

    def budget(self, setup) -> None:
        """Oversized serving neighborhoods fail closed before MAGE expansion."""
        features, mask, g = setup
        with pytest.raises(Net, match="exceeding serving budget"):
            expand(g, [1, 3], 0, features, mask, iters=3, max_nodes=2)

    def loop(self, setup) -> None:
        features, mask, _ = setup
        g_loopy = sp.csr_matrix(np.eye(3, dtype=np.float32))
        with pytest.raises(Net, match="graph has self-loops"):
            expand(g_loopy, [0, 2], 0, features, mask[:3], iters=3)

    def articulation(self) -> None:
        """Removal candidates use cut vertices rather than repeated BFS checks."""
        path = sp.csr_matrix(np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.float32))
        triangle = sp.csr_matrix(np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=np.float32))
        assert _articulation_points({0, 1, 2}, neighbors_map(path)) == {1}
        assert _articulation_points({0, 1, 2}, neighbors_map(triangle)) == set()
