"""Property-based tests using Hypothesis."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from morel.data.build import bipartite, cooccurrence
from morel.data.mask import bernoulli
from morel.retrieve.acs import compute
from morel.retrieve.bfs import path
from morel.route import Dense, Gumbel, Top


@st.composite
def random(draw: st.DrawFn) -> sp.csr_matrix:
    n = draw(st.integers(min_value=2, max_value=12))
    arr = np.zeros((n, n), dtype=np.float32)
    for i in range(n - 1):
        if draw(st.booleans()):
            arr[i, i + 1] = 1
            arr[i + 1, i] = 1
    return sp.csr_matrix(arr)


@st.composite
def random_bipartite(draw: st.DrawFn) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Generate a bounded interaction graph, including duplicate edges."""
    users = draw(st.integers(min_value=1, max_value=8))
    items = draw(st.integers(min_value=1, max_value=8))
    edges = draw(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=7),
                st.integers(min_value=0, max_value=7),
            ),
            max_size=32,
        )
    )
    user = np.array([u % users for u, _ in edges], dtype=np.int64)
    item = np.array([i % items for _, i in edges], dtype=np.int64)
    return user, item, users, items


class Checker:
    """Aggregated test methods for this module."""

    @given(random(), st.integers(min_value=0, max_value=10))
    @settings(max_examples=10, deadline=None)
    def acs(self, graph: sp.csr_matrix, anchor: int) -> None:
        if graph.shape[0] == 0:
            return
        anchor = anchor % graph.shape[0]
        sub = compute(graph, [anchor], fallback="empty")
        assert anchor in sub

    @given(st.integers(min_value=2, max_value=20))
    @settings(max_examples=5, deadline=None)
    def bernoulli(self, items: int) -> None:
        mask = bernoulli(items, 3, 0.4, seed=0).numpy()
        assert (mask.sum(axis=1) >= 1).all()

    @given(random_bipartite())
    @settings(max_examples=15, deadline=None)
    def cooccurrence(self, payload: tuple[np.ndarray, np.ndarray, int, int]) -> None:
        """Co-occurrence remains a simple, loop-free binary graph."""
        user, item, users, items = payload
        graph = bipartite(user, item, users, items)
        result = cooccurrence(graph).toarray()
        assert result.shape == (items, items)
        assert np.array_equal(result, result.T)
        assert np.all(np.diag(result) == 0)
        assert np.isin(result, [0, 1]).all()

    @given(st.integers(min_value=-2, max_value=10), st.integers(min_value=-2, max_value=10))
    @settings(max_examples=20, deadline=None)
    def bipartite_bounds(self, user_id: int, item_id: int) -> None:
        """Malformed sparse-graph indices become domain errors, never SciPy leaks."""
        users, items = 4, 5
        user = np.array([user_id], dtype=np.int64)
        item = np.array([item_id], dtype=np.int64)
        valid = 0 <= user_id < users and 0 <= item_id < items
        if valid:
            graph = bipartite(user, item, users, items)
            assert graph.shape == (users, items)
        else:
            from morel.core.errors import Datum

            with pytest.raises(Datum):
                bipartite(user, item, users, items)

    def top(self) -> None:
        r = Top(dim=8, k=10, p=3, tau=0.5)
        torch.manual_seed(0)
        for _ in range(5):
            x = torch.randn(4, 8)
            out = r(x, training=True)
            assert torch.allclose(out.probs.sum(-1), torch.ones(4), atol=1e-5)

    def dense(self) -> None:
        r = Dense(dim=8, k=10, tau=0.5)
        torch.manual_seed(0)
        for _ in range(5):
            x = torch.randn(4, 8)
            out = r(x, training=True)
            assert torch.allclose(out.probs.sum(-1), torch.ones(4), atol=1e-5)

    def gumbel(self) -> None:
        r = Gumbel(dim=8, k=10, tau=0.5)
        torch.manual_seed(0)
        for _ in range(5):
            x = torch.randn(4, 8)
            out = r(x, training=True)
            assert torch.allclose(out.probs.sum(-1), torch.ones(4), atol=1e-5)

    def temperature(self) -> None:
        """Lower temperature sharpens the routing distribution."""
        torch.manual_seed(0)
        x = torch.randn(8, 8)
        soft = Gumbel(dim=8, k=10, tau=2.0)(x, training=False).probs
        sharp = Gumbel(dim=8, k=10, tau=0.1)(x, training=False).probs
        soft_entropy = -(soft * torch.log(soft + 1e-12)).sum(-1).mean()
        sharp_entropy = -(sharp * torch.log(sharp + 1e-12)).sum(-1).mean()
        assert sharp_entropy < soft_entropy

    @given(random(), st.integers(min_value=0, max_value=10), st.integers(min_value=0, max_value=10))
    @settings(max_examples=5, deadline=None)
    def bfs(self, graph: sp.csr_matrix, start: int, end: int) -> None:
        if graph.shape[0] == 0:
            return
        start = start % graph.shape[0]
        end = end % graph.shape[0]
        p = path(graph, start, end)
        assert all(0 <= n < graph.shape[0] for n in p)
