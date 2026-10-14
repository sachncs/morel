"""Build a serving pipeline from an immutable run artifact directory."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from morel.core.config import Config
from morel.core.errors import Model
from morel.data.store import MAX_ARTIFACT_BYTES, load_graph, load_npz
from morel.pipeline import Pipeline
from morel.train.checkpoint import State


def _load_mask(path: Path) -> np.ndarray:
    """Load a serving mask while keeping corruption inside the model boundary.

    Args:
        path: Path to the persisted mask array.

    Returns:
        A finite, numeric, two-dimensional mask.

    Raises:
        Model: If the artifact is missing, oversized, unreadable, or invalid.
    """
    if not path.exists():
        raise Model(f"serving mask artifact not found: {path}")
    try:
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            raise Model(
                f"serving mask artifact exceeds the {MAX_ARTIFACT_BYTES}-byte limit: {path}"
            )
        mask = np.load(path, allow_pickle=False)
    except Model:
        raise
    except (OSError, EOFError, OverflowError, TypeError, ValueError) as exc:
        raise Model(f"invalid serving mask artifact: {path}") from exc
    if not isinstance(mask, np.ndarray) or mask.ndim != 2:
        raise Model("serving mask artifact must be a 2-D array")
    if not np.issubdtype(mask.dtype, np.number) or not np.isfinite(mask).all():
        raise Model("serving mask artifact must contain finite numeric values")
    return mask


def _validate_features(features: dict[str, np.ndarray]) -> None:
    """Validate serving feature arrays before their shapes reach the pipeline."""
    if not features:
        raise Model("serving feature artifact is empty")
    if any(
        value.ndim != 2 or not np.issubdtype(value.dtype, np.number) or not np.isfinite(value).all()
        for value in features.values()
    ):
        raise Model("serving feature artifact arrays must be finite 2-D numeric arrays")
    row_counts = {int(value.shape[0]) for value in features.values()}
    if len(row_counts) != 1:
        raise Model("serving feature arrays must share a row count")


def from_run(directory: Path | str) -> Pipeline:
    """Load and validate a pipeline from a completed run directory.

    A serving bundle contains ``config.yaml``, ``best.pt``,
    ``features.npz``, ``mask.npy``, ``item_graph.npz`` and
    ``bipartite.npz``. Missing or incompatible artifacts raise a model error
    before the HTTP server accepts traffic.
    """
    root = Path(directory)
    config = Config.load(root / "config.yaml")
    features = load_npz(root / "features.npz", expected_config_hash=config.hash())
    _validate_features(features)
    mask = _load_mask(root / "mask.npy")
    if mask.shape[0] != next(iter(features.values())).shape[0]:
        raise Model("serving mask does not match the feature corpus")
    if mask.shape[1] != len(features):
        raise Model("serving mask modality count does not match features")

    item_graph = load_graph(root / "item_graph.npz", expected_config_hash=config.hash())
    ui_graph = load_graph(root / "bipartite.npz", expected_config_hash=config.hash())
    dims = {name: int(value.shape[1]) for name, value in features.items()}
    pipeline = Pipeline(config, dims=dims)
    pipeline.attach(features, mask.astype(np.float32, copy=False), item_graph)
    pipeline.wire(ui_graph, feature_dim=sum(dims.values()))
    pipeline.set_retrieval_budget(config.serve.retrieval_max_nodes)

    checkpoint = root / "best.pt"
    state = State.load(checkpoint, expected_config_hash=config.hash())
    keys = set(state.model)
    pipeline_keys = set(pipeline.state_dict())
    if keys & pipeline_keys:
        pipeline.load_state_dict(state.model, strict=False)
    else:
        if pipeline.recommender is None:
            raise Model("serving pipeline has no recommender")
        pipeline.recommender.load_state_dict(state.model)
    pipeline.eval()
    pe_path = root / "pe.npz"
    if pe_path.exists():
        payload = load_npz(pe_path, expected_config_hash=config.hash())
        encoding = payload.get("encoding")
        if encoding is None or set(payload) != {"encoding"}:
            raise Model("serving positional-encoding artifact must contain only 'encoding'")
        if pipeline.cadj is None:
            raise Model("serving item graph is missing for positional encoding")
        pipeline.encoder.prime(pipeline.cadj, encoding)
    else:
        pipeline.warmup()
    return pipeline


__all__ = ["from_run"]
