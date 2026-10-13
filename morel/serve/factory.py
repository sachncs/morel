"""Build a serving pipeline from an immutable run artifact directory."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from morel.core.config import Config
from morel.core.errors import Model
from morel.data.store import load_graph, load_npz
from morel.pipeline import Pipeline
from morel.train.checkpoint import State


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
    mask_path = root / "mask.npy"
    if not mask_path.exists():
        raise Model(f"serving mask artifact not found: {mask_path}")
    mask = np.load(mask_path, allow_pickle=False)
    if not features:
        raise Model("serving feature artifact is empty")
    if mask.ndim != 2 or mask.shape[0] != next(iter(features.values())).shape[0]:
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
