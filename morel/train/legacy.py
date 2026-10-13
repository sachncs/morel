"""Explicit compatibility loader for trusted legacy checkpoints.

This module is deliberately separate from the production checkpoint API.
Anything loaded here is deserialized with Python pickle semantics and may
execute code embedded in the file. Callers must opt in at the call site and
must only use artifacts from a trusted origin.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import torch

from morel.core.errors import Cfg, Model


def load_trusted(target: Path | str, *, acknowledge_risk: bool = False) -> dict[str, Any]:
    """Load a legacy checkpoint containing arbitrary Python objects.

    Args:
        target: Path to a trusted legacy checkpoint.
        acknowledge_risk: Explicit acknowledgement that pickle can execute
            code while loading the file.

    Returns
    -------
        The legacy checkpoint mapping.

    Raises
    ------
        Cfg: If the caller did not explicitly acknowledge the risk.
        FileNotFoundError: If ``target`` does not exist.
        Model: If the loaded value is not a mapping.
    """
    if not acknowledge_risk:
        raise Cfg(
            "trusted legacy checkpoint loading requires acknowledge_risk=True; "
            "use morel.train.checkpoint.load() for production checkpoints"
        )
    warnings.warn(
        "trusted legacy checkpoint loading executes pickle; use only trusted files",
        RuntimeWarning,
        stacklevel=2,
    )
    path = Path(target)
    if not path.exists():
        raise FileNotFoundError(path)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        raise Model(f"legacy checkpoint at {path} must be a dict, got {type(payload).__name__}")
    return payload


__all__ = ["load_trusted"]
