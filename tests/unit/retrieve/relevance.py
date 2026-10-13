"""Tests for morel.retrieve.relevance."""

from __future__ import annotations

import numpy as np
import pytest

from morel.retrieve.relevance import prepare, rel, relevance


class Checker:
    """Aggregated test methods for this module."""

    def one(self) -> None:
        f = {"v": np.eye(3, dtype=np.float32)}
        m = np.ones((3, 1), dtype=np.float32)
        assert relevance(0, 0, f, m) == 1.0

    def zero(self) -> None:
        f = {"v": np.eye(2, dtype=np.float32)}
        m = np.ones((2, 1), dtype=np.float32)
        assert relevance(0, 1, f, m) == 0.0

    def modality(self) -> None:
        f = {"v": np.eye(2, dtype=np.float32)}
        m = np.zeros((2, 1), dtype=np.float32)
        assert relevance(0, 1, f, m) == 0.0

    def self(self) -> None:
        f = {"v": np.eye(2, dtype=np.float32)}
        m = np.ones((2, 1), dtype=np.float32)
        val = rel(0, np.array([0, 1]), f, m)
        assert val == 0.0

    def returns(self) -> None:
        f = {"v": np.eye(2, dtype=np.float32)}
        m = np.ones((2, 1), dtype=np.float32)
        assert rel(0, np.array([], dtype=np.int64), f, m) == 0.0

    def excludes_unshared(self) -> None:
        """Candidates without a joint modality must not dilute the mean."""
        features = {
            "v": np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
            "t": np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]], dtype=np.float32),
        }
        mask = np.array([[1, 0], [1, 0], [0, 1]], dtype=np.float32)
        assert rel(0, np.array([1, 2]), features, mask) == 1.0

    def python(self) -> None:
        """Vectorised rel produces the same numerical result as the legacy loop."""
        rng = np.random.default_rng(0)
        items, dim = 16, 5
        features = {
            "v": rng.normal(size=(items, dim)).astype(np.float32),
            "t": rng.normal(size=(items, dim)).astype(np.float32),
        }
        mask = np.ones((items, 2), dtype=np.float32)
        mask[7, 0] = 0
        nodes = np.array([3, 5, 7, 9, 0], dtype=np.int64)

        expected = float(
            np.mean([relevance(2, int(v), features, mask) for v in nodes if int(v) != 2])
        )
        actual = rel(2, nodes, features, mask)
        assert abs(actual - expected) < 1e-6

    def prepared(self) -> None:
        """Prepared relevance matches the public one-shot calculation."""
        rng = np.random.default_rng(1)
        features = {"v": rng.normal(size=(8, 3)).astype(np.float32)}
        mask = np.ones((8, 1), dtype=np.float32)
        nodes = np.array([1, 3, 6], dtype=np.int64)
        assert prepare(features, mask).score(2, nodes) == rel(2, nodes, features, mask)

    def cached_query_scores(self) -> None:
        """Repeated candidate scoring reuses one query-wide relevance pass."""
        rng = np.random.default_rng(2)
        features = {"v": rng.normal(size=(8, 3)).astype(np.float32)}
        mask = np.ones((8, 1), dtype=np.float32)
        index = prepare(features, mask)
        nodes = np.array([0, 1, 3, 6], dtype=np.int64)
        assert index.score(2, nodes) == pytest.approx(index.score(2, nodes[::-1]))
        assert list(index._query_scores) == [2]
