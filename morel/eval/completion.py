"""Completion quality metrics."""

from __future__ import annotations

from morel.core.types import Array


def mse(predictions: Array, targets: Array) -> float:
    """Mean squared error."""
    return float(((predictions - targets) ** 2).mean())


def modal(predictions: dict[str, Array], targets: dict[str, Array]) -> dict[str, float]:
    """Per-modality mean squared error."""
    out: dict[str, float] = {}
    for name, pred in predictions.items():
        target = targets[name]
        out[name] = float(((pred - target) ** 2).mean())
    return out


def variance(predictions: Array, targets: Array) -> float:
    """Explained variance score in ``(-inf, 1]``."""
    if predictions.shape != targets.shape:
        raise ValueError(f"shape mismatch: {predictions.shape} vs {targets.shape}")
    var_y = float(targets.var())
    if var_y == 0.0:
        return 0.0
    return float(1.0 - ((targets - predictions).var() / var_y))


__all__ = ["modal", "mse", "variance"]
