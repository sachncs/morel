"""Tests for morel.data.store."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from morel.core.errors import Datum
from morel.data.manifest import Manifest
from morel.data.store import (
    MAX_ARTIFACT_BYTES,
    MAX_GRAPH_NODES,
    load_graph,
    load_npz,
    save_graph,
    store,
)


class Checker:
    """Aggregated test methods for this module."""

    def roundtrip(self, tmp_path: Path) -> None:
        target = tmp_path / "x.npz"
        store(target, a=np.arange(4, dtype=np.float32), b=np.ones(4))
        loaded = load_npz(target)
        assert np.array_equal(loaded["a"], np.arange(4))
        assert np.array_equal(loaded["b"], np.ones(4))

    def manifest(self, tmp_path: Path) -> None:
        target = tmp_path / "x.npz"
        m = Manifest(
            dataset="Beauty", version="1", code="c", seed=0, extractor="text", cfg_hash="abc"
        )
        store(target, manifest_obj=m, a=np.arange(2, dtype=np.float32))
        assert load_npz(target).get("a") is not None

    def raises(self, tmp_path: Path) -> None:
        with pytest.raises(Datum):
            load_npz(tmp_path / "missing.npz")

    def graph(self, tmp_path: Path) -> None:
        target = tmp_path / "g.npz"
        g = sp.csr_matrix(np.eye(4, dtype=np.float32))
        save_graph(target, g)
        out = load_graph(target)
        assert out.shape == (4, 4)
        assert np.allclose(out.toarray(), np.eye(4))

    def missing(self, tmp_path: Path) -> None:
        with pytest.raises(Datum):
            load_graph(tmp_path / "missing.npz")

    def empty(self, tmp_path: Path) -> None:
        with pytest.raises(Datum):
            store(tmp_path / "x.npz")

    def malformed(self, tmp_path: Path) -> None:
        broken = tmp_path / "broken.npz"
        broken.write_bytes(b"not an npz archive")
        with pytest.raises(Datum, match="invalid npz"):
            load_npz(broken)

    def byte_bound(self, tmp_path: Path) -> None:
        """NPZ loaders reject oversized archives before decompression."""
        oversized = tmp_path / "oversized.npz"
        with oversized.open("wb") as handle:
            handle.truncate(MAX_ARTIFACT_BYTES + 1)
        with pytest.raises(Datum, match="exceeds"):
            load_npz(oversized)
        with pytest.raises(Datum, match="exceeds"):
            load_graph(oversized)

    def invalid_graph(self, tmp_path: Path) -> None:
        target = tmp_path / "bad-graph.npz"
        np.savez(
            target,
            data=np.ones(2),
            row=np.array([0, 3]),
            col=np.array([0, 1]),
            shape=np.array([2, 2]),
        )
        with pytest.raises(Datum, match="outside its shape"):
            load_graph(target)

    def invalid_graph_values(self, tmp_path: Path) -> None:
        target = tmp_path / "bad-values.npz"
        np.savez(
            target,
            data=np.array([np.nan]),
            row=np.array([0.0]),
            col=np.array([0]),
            shape=np.array([2, 2]),
        )
        with pytest.raises(Datum, match="integer arrays"):
            load_graph(target)

    def graph_bounds(self, tmp_path: Path) -> None:
        """Declared sparse dimensions and edge counts are bounded."""
        too_wide = tmp_path / "too-wide.npz"
        np.savez(
            too_wide,
            data=np.array([], dtype=np.float32),
            row=np.array([], dtype=np.int64),
            col=np.array([], dtype=np.int64),
            shape=np.array([MAX_GRAPH_NODES + 1, MAX_GRAPH_NODES + 1]),
        )
        with pytest.raises(Datum, match="node artifact limit"):
            load_graph(too_wide)

        too_many_edges = tmp_path / "too-many-edges.npz"
        np.savez(
            too_many_edges,
            data=np.ones(2, dtype=np.float32),
            row=np.array([0, 1], dtype=np.int64),
            col=np.array([1, 0], dtype=np.int64),
            shape=np.array([2, 2]),
        )
        with pytest.raises(Datum, match="edge artifact limit"):
            # The optional bound makes this test small and deterministic.
            load_graph(too_many_edges, max_edges=1)
