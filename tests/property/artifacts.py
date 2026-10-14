"""Property checks for malformed sparse artifact boundaries."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from morel.core.errors import Datum
from morel.data.store import load_graph, load_npz


class Checker:
    """Aggregated property tests for sparse artifact loading."""

    @given(
        st.lists(st.integers(min_value=-4, max_value=8), max_size=8),
        st.lists(st.integers(min_value=-4, max_value=8), max_size=8),
        st.lists(st.floats(allow_nan=True, allow_infinity=True, width=32), max_size=8),
        st.lists(st.integers(min_value=-2, max_value=8), min_size=0, max_size=3),
    )
    @settings(max_examples=30, deadline=None)
    def malformed_graph_never_leaks_internal_errors(
        self,
        rows: list[int],
        cols: list[int],
        weights: list[float],
        shape: list[int],
    ) -> None:
        """Arbitrary safe NumPy payloads reject as ``Datum`` or load safely."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "fuzz-graph.npz"
            np.savez(
                path,
                data=np.asarray(weights),
                row=np.asarray(rows),
                col=np.asarray(cols),
                shape=np.asarray(shape),
            )
            try:
                graph = load_graph(path)
            except Datum:
                return
            assert graph.ndim == 2
            assert graph.shape[0] >= 0
            assert graph.shape[1] >= 0

    @given(st.binary(max_size=512))
    @settings(max_examples=30, deadline=None)
    def malformed_npz_never_leaks_internal_errors(self, payload: bytes) -> None:
        """Arbitrary artifact bytes reject as ``Datum`` or load as mappings."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "fuzz-arrays.npz"
            path.write_bytes(payload)
            try:
                arrays = load_npz(path)
            except Datum:
                return
            assert isinstance(arrays, dict)
