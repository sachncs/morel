"""Ablation conditions as configuration transforms.

``config.eval.ablations`` names the conditions an experiment should compare,
but nothing could turn a name into a runnable setup: the names were inert
strings. An ablation is precisely "the same configuration with one component
removed", so each condition is registered here as a function from a ``Config``
to an ablated ``Config``.

Expressing ablations this way means a condition runs through exactly the same
pipeline as the baseline, with only the named component changed. Nothing about
the ablation lives in the model code, so a new condition needs no change to
the pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from morel.core.config import Config
from morel.core.factory import FactoryRegistry

#: Name used for the unmodified configuration in an ablation sweep.
BASELINE = "baseline"


def noretry(config: Config) -> Config:
    """Remove graph retrieval, leaving each item to be completed on its own."""
    return replace(config, retrieve=replace(config.retrieve, kind="none"))


def nope(config: Config) -> Config:
    """Remove the Laplacian positional encoding by requesting zero dimensions."""
    return replace(config, encode=replace(config.encode, pe=0))


def nobook(config: Config) -> Config:
    """Replace the codebook with a pass-through, removing quantization."""
    return replace(config, codebook=replace(config.codebook, kind="identity"))


#: Map from ablation name to transform function. Module-local; no global registry.
KIND: dict[str, Callable[[Config], Config]] = {
    "noretry": noretry,
    "nope": nope,
    "nobook": nobook,
}

_ABLATION_REGISTRY = FactoryRegistry[Config]("ablation", KIND)


def ablate(config: Config, name: str) -> Config:
    """Return ``config`` with the named ablation applied.

    Args:
        config: Baseline configuration.
        name: A registered ablation name, or :data:`BASELINE` for no change.

    Returns:
        The ablated configuration. The input is never mutated.

    Raises:
        Cfg: If ``name`` is not a registered ablation.
    """
    if name == BASELINE:
        return config
    return _ABLATION_REGISTRY.resolve(name)(config)


def conditions(config: Config) -> tuple[str, ...]:
    """Return the sweep's condition names: the baseline then each ablation."""
    return (BASELINE, *config.eval.ablations)


__all__ = [
    "BASELINE",
    "KIND",
    "ablate",
    "conditions",
    "nobook",
    "nope",
    "noretry",
]
