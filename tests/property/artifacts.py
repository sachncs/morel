"""Property checks for malformed sparse artifact boundaries."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import scipy.sparse as sp
from hypothesis import given, settings
from hypothesis import strategies as st

from morel.core.errors import Datum, Model
from morel.data.store import MAX_GRAPH_NODES, load_graph, load_npz, save_graph
from morel.serve.factory import _load_mask


class Checker:
    """Aggregated property tests for sparse artifact loading."""

    @given(
        st.lists(st.integers(min_value=-4, max_value=8), max_size=8),
        st.lists(st.integers(min_value=-4, max_value=8), max_size=8),
        st.lists(st.floats(allow_nan=True, allow_infinity=True, width=32), max_size=8),
        st.lists(st.integers(min_value=-2, max_value=8), min_size=0, max_size=3),
    )
    @settings(max_examples=100, deadline=None)
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

    @given(
        st.integers(min_value=0, max_value=8),
        st.lists(st.integers(min_value=0, max_value=7), max_size=16),
        st.lists(st.integers(min_value=0, max_value=7), max_size=16),
        st.lists(
            st.floats(min_value=-2, max_value=2, allow_nan=False, allow_infinity=False), max_size=16
        ),
    )
    @settings(max_examples=100, deadline=None)
    def sparse_roundtrip_edge_matrix(
        self,
        size: int,
        rows: list[int],
        cols: list[int],
        weights: list[float],
    ) -> None:
        """Valid sparse edge cases survive atomic persistence and reload."""
        count = min(len(rows), len(cols), len(weights))
        rows = [row % size for row in rows[:count]] if size else []
        cols = [col % size for col in cols[:count]] if size else []
        weights = weights[:count] if size else []
        graph = sp.coo_matrix(
            (np.asarray(weights, dtype=np.float32), (rows, cols)), shape=(size, size)
        ).tocsr()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "roundtrip-graph.npz"
            save_graph(path, graph)
            loaded = load_graph(path)
        assert loaded.shape == graph.shape
        assert np.isfinite(loaded.data).all()
        assert np.array_equal(loaded.toarray(), graph.toarray())

    @given(st.binary(max_size=512))
    @settings(max_examples=100, deadline=None)
    def malformed_npz_never_leaks_internal_errors(self, payload: bytes) -> None:
        """Arbitrary artifact bytes reject as ``Datum`` or load as mappings."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "fuzz-arrays.npz"
            path.write_bytes(payload)
            try:
                arrays = load_npz(path)
            except Datum:
                arrays = None
            if arrays is not None:
                assert isinstance(arrays, dict)
            try:
                graph = load_graph(path)
            except Datum:
                return
            assert graph.ndim == 2

    @given(st.binary(max_size=4096))
    @settings(max_examples=100, deadline=None)
    def malformed_manifest_sidecar_never_leaks_internal_errors(self, payload: bytes) -> None:
        """Corrupt sidecars reject as ``Datum`` or preserve a valid artifact load."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sidecar-graph.npz"
            np.savez(path, values=np.asarray([1], dtype=np.int64))
            path.with_suffix(path.suffix + ".manifest.json").write_bytes(payload)
            try:
                arrays = load_npz(path)
            except Datum:
                return
            assert isinstance(arrays, dict)

    @given(st.binary(max_size=512))
    @settings(max_examples=100, deadline=None)
    def malformed_mask_never_leaks_internal_errors(self, payload: bytes) -> None:
        """Arbitrary mask bytes reject as ``Model`` or load as valid arrays."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "random-mask.npy"
            path.write_bytes(payload)
            try:
                mask = _load_mask(path)
            except Model:
                return
            assert mask.ndim == 2
            assert np.issubdtype(mask.dtype, np.number)
            assert np.isfinite(mask).all()

    @given(st.integers(min_value=MAX_GRAPH_NODES + 1, max_value=MAX_GRAPH_NODES + 1024))
    @settings(max_examples=20, deadline=None)
    def oversized_graph_metadata_fails_before_allocation(self, oversized: int) -> None:
        """Graph dimensions over the safety bound become typed data errors."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "oversized-graph.npz"
            np.savez(
                path,
                data=np.asarray([], dtype=np.float32),
                row=np.asarray([], dtype=np.int64),
                col=np.asarray([], dtype=np.int64),
                shape=np.asarray([oversized, 1], dtype=np.int64),
            )
            try:
                load_graph(path)
            except Datum:
                return
            raise AssertionError("oversized graph metadata was accepted")

    def oversized_graph_edge_count_fails_before_sparse_build(self) -> None:
        """Graph coordinate counts over the caller budget fail closed."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "oversized-edges.npz"
            np.savez(
                path,
                data=np.ones(5, dtype=np.float32),
                row=np.zeros(5, dtype=np.int64),
                col=np.zeros(5, dtype=np.int64),
                shape=np.asarray([2, 2], dtype=np.int64),
            )
            try:
                load_graph(path, max_edges=4)
            except Datum:
                return
            raise AssertionError("oversized graph edge metadata was accepted")
