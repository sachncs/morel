"""Atomic save/load for data artifacts with manifest verification."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from morel.core.errors import Datum
from morel.core.types import Array
from morel.data import manifest

# Defensive defaults for persisted sparse graphs. These are intentionally
# generous for the supported research datasets while preventing malformed
# metadata from requesting an unbounded sparse-matrix shape or edge list.
MAX_GRAPH_NODES = 10_000_000
MAX_GRAPH_EDGES = 50_000_000
MAX_ARTIFACT_BYTES = 1 << 30


def _check_artifact_size(path: Path, max_bytes: int) -> None:
    """Reject an artifact before opening or decompressing its arrays."""
    if max_bytes <= 0:
        raise ValueError("artifact byte bound must be positive")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise Datum(f"unable to stat artifact: {path}") from exc
    if size > max_bytes:
        raise Datum(f"artifact exceeds the {max_bytes}-byte limit: {path}")


def _check_graph_bounds(
    shape: tuple[int, int],
    edges: int,
    path: Path,
    *,
    max_nodes: int = MAX_GRAPH_NODES,
    max_edges: int = MAX_GRAPH_EDGES,
) -> None:
    """Reject sparse graph dimensions that exceed the artifact contract."""
    if max_nodes <= 0 or max_edges <= 0:
        raise ValueError("graph artifact bounds must be positive")
    if any(size > max_nodes for size in shape):
        raise Datum(f"graph shape {shape} exceeds the {max_nodes}-node artifact limit: {path}")
    if edges > max_edges:
        raise Datum(
            f"graph has {edges} edges, exceeding the {max_edges}-edge artifact limit: {path}"
        )


def atomic(target: Path, writer: Callable[[Path], None]) -> Path:
    """Write to a sibling tempfile, then atomically replace the target.

    The tempfile name is constructed so that ``np.savez`` and ``sp.store``
    do not silently append a ``.npz`` suffix. Both libraries append ``.npz``
    when the path does not already end in that suffix; we therefore keep the
    target's suffix in the tempfile name.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix or ".tmp"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=target.stem + ".", dir=target.parent)
    os.close(fd)
    try:
        writer(Path(tmp_path))
        os.replace(tmp_path, target)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return target


def store(
    target: Path | str,
    *,
    manifest_obj: manifest.Manifest | None = None,
    **arrays: Array,
) -> Path:
    """Atomically save one or more numpy arrays plus an optional manifest.

    Args:
        target: Destination ``.npz`` path.
        manifest_obj: Optional manifest to save as a sidecar.
        **arrays: Named arrays to include.

    Returns:
        The destination path.
    """
    if not arrays:
        raise Datum("store requires at least one array")
    final = Path(target).resolve()
    # A key literally named ``allow_pickle`` would bind to savez's own keyword;
    # that raises rather than silently dropping data, so the narrowing is safe.
    atomic(final, lambda tmp: np.savez(tmp, **arrays))  # type: ignore[arg-type]
    if manifest_obj is not None:
        manifest.save(final, manifest_obj)
    return final


def load_npz(
    target: Path | str,
    *,
    expected_config_hash: str | None = None,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> dict[str, Array]:
    """Load a ``.npz`` artifact and verify the manifest if present.

    Args:
        target: Path to the ``.npz`` file.
        expected_config_hash: If set, raise on manifest mismatch.
        max_bytes: Maximum compressed artifact size accepted before loading.

    Returns:
        Dict mapping array names to numpy arrays.
    """
    path = Path(target)
    if not path.exists():
        raise Datum(f"npz artifact not found: {path}")
    _check_artifact_size(path, max_bytes)
    if manifest.locate(path).exists():
        manifest.load(path, expected_config_hash=expected_config_hash)
    try:
        with np.load(path, allow_pickle=False) as npz:
            return {key: npz[key] for key in npz.files}
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise Datum(f"invalid npz artifact: {path}") from exc


def save_graph(
    target: Path | str,
    graph: sp.spmatrix,
    *,
    manifest_obj: manifest.Manifest | None = None,
) -> Path:
    """Atomically save a sparse graph with manifest.

    Stores data, indices, indptr, and shape as a regular npz so that the
    file can be loaded without scipy's filename-suffix shenanigans.
    """
    final = Path(target).resolve()
    coo = sp.coo_matrix(graph)
    graph_shape = (int(coo.shape[0]), int(coo.shape[1]))
    _check_graph_bounds(graph_shape, int(coo.nnz), final)

    def writer(tmp: Path) -> None:
        """Write the sparse graph to a temp .npz file.

        Args:
            tmp: Temporary file path to write to.
        """
        np.savez(
            tmp,
            data=coo.data.astype(np.float32, copy=False),
            row=coo.row.astype(np.int64, copy=False),
            col=coo.col.astype(np.int64, copy=False),
            shape=np.asarray(coo.shape, dtype=np.int64),
        )

    atomic(final, writer)
    if manifest_obj is not None:
        manifest.save(final, manifest_obj)
    return final


def load_graph(
    target: Path | str,
    *,
    expected_config_hash: str | None = None,
    max_nodes: int = MAX_GRAPH_NODES,
    max_edges: int = MAX_GRAPH_EDGES,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> sp.spmatrix:
    """Load a sparse graph, verify its manifest, and enforce size bounds.

    Args:
        target: Path to the graph artifact.
        expected_config_hash: Optional manifest hash to require.
        max_nodes: Maximum number of rows or columns accepted.
        max_edges: Maximum number of stored coordinate entries accepted.
        max_bytes: Maximum compressed artifact size accepted before loading.
    """
    path = Path(target)
    if not path.exists():
        raise Datum(f"graph artifact not found: {path}")
    _check_artifact_size(path, max_bytes)
    if manifest.locate(path).exists():
        manifest.load(path, expected_config_hash=expected_config_hash)
    try:
        with np.load(path, allow_pickle=False) as npz:
            data = npz["data"]
            row = npz["row"]
            col = npz["col"]
            raw_shape = npz["shape"]
        if any(array.ndim != 1 for array in (data, row, col)):
            raise Datum(f"graph arrays must be one-dimensional: {path}")
        if len(row) != len(col) or len(data) != len(row):
            raise Datum(f"graph arrays have inconsistent lengths: {path}")
        if not all(np.issubdtype(array.dtype, np.integer) for array in (row, col, raw_shape)):
            raise Datum(f"graph coordinates and shape must be integer arrays: {path}")
        if not np.issubdtype(data.dtype, np.number) or not np.isfinite(data).all():
            raise Datum(f"graph weights must be finite numeric values: {path}")
        if raw_shape.ndim != 1 or raw_shape.size != 2:
            raise Datum(f"graph shape must contain two dimensions: {path}")
        shape = (int(raw_shape[0]), int(raw_shape[1]))
        if any(size < 0 for size in shape):
            raise Datum(f"graph shape cannot be negative: {path}")
        _check_graph_bounds(
            shape,
            len(row),
            path,
            max_nodes=max_nodes,
            max_edges=max_edges,
        )
        if len(row) and (
            np.any(row < 0) or np.any(col < 0) or np.any(row >= shape[0]) or np.any(col >= shape[1])
        ):
            raise Datum(f"graph coordinates are outside its shape: {path}")
        coo = sp.coo_matrix((data, (row, col)), shape=shape)
    except Datum:
        raise
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise Datum(f"invalid graph artifact: {path}") from exc
    return coo.tocsr()


__all__ = [
    "MAX_ARTIFACT_BYTES",
    "MAX_GRAPH_EDGES",
    "MAX_GRAPH_NODES",
    "load_graph",
    "load_npz",
    "save_graph",
    "store",
]
