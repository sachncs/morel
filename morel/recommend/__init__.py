"""Public API for the morel.recommend package."""

from collections.abc import Callable

import torch.nn as nn

from morel.core.factory import FactoryRegistry, _accepts_keywords, _validate_implementation
from morel.recommend.baseline import MF, Pop
from morel.recommend.bpr import bpr, distinct, negatives, to_ranks
from morel.recommend.light import Light
from morel.recommend.protocol import FeatureAware, Fits, Normalizes, Recommender


def build(
    kind: str,
    *,
    users: int,
    items: int,
    embed: int,
    layers: int,
    feature_dim: int | None = None,
    seed: int | None = None,
) -> nn.Module:
    """Build the downstream ranker selected by ``config.recommend.kind``.

    Args:
        kind: Ranker name. One of ``"light"``, ``"mf"``, ``"pop"``.
        users: Number of users.
        items: Number of items.
        embed: Embedding dimension.
        layers: Number of propagation layers (ignored for non-graph rankers).
        feature_dim: Optional modality feature dimension for ``"light"``.
        seed: Optional RNG seed.

    Returns:
        The constructed ranker module.

    Raises:
        ValueError: If ``kind`` is not a known ranker name.
    """
    return _FACTORIES.build(
        kind,
        users=users,
        items=items,
        embed=embed,
        layers=layers,
        feature_dim=feature_dim,
        seed=seed,
    )


#: Map from config name to ranker class for introspection.
KIND: dict[str, type[nn.Module]] = {
    "light": Light,
    "mf": MF,
    "pop": Pop,
}


def register(
    kind: str, factory: Callable[..., nn.Module], *, implementation: type[nn.Module]
) -> None:
    """Register an additive recommender implementation under a new config name."""
    _validate_implementation(implementation, Recommender, "recommender")
    _FACTORIES.register(kind, factory)
    KIND[kind] = implementation


def _build_light(
    *,
    users: int,
    items: int,
    embed: int,
    layers: int,
    feature_dim: int | None,
    seed: int | None,
) -> nn.Module:
    """Adapt the shared constructor shape to the graph ranker."""
    return Light(
        users=users,
        items=items,
        embed=embed,
        layers=layers,
        feature_dim=feature_dim,
        seed=seed,
    )


def _build_mf(
    *,
    users: int,
    items: int,
    embed: int,
    layers: int,
    feature_dim: int | None,
    seed: int | None,
) -> nn.Module:
    """Adapt the shared constructor shape to matrix factorization."""
    del layers, feature_dim
    return MF(users=users, items=items, embed=embed, seed=seed)


def _build_pop(
    *,
    users: int,
    items: int,
    embed: int,
    layers: int,
    feature_dim: int | None,
    seed: int | None,
) -> nn.Module:
    """Adapt the shared constructor shape to popularity ranking."""
    del embed, layers, feature_dim, seed
    return Pop(users=users, items=items)


_FACTORIES = FactoryRegistry[nn.Module](
    "recommender",
    {"light": _build_light, "mf": _build_mf, "pop": _build_pop},
    validator=lambda value: isinstance(value, Recommender),
    factory_validator=lambda value: _accepts_keywords(
        value, ("users", "items", "embed", "layers", "feature_dim", "seed")
    ),
)


__all__ = [
    "KIND",
    "MF",
    "FeatureAware",
    "Fits",
    "Light",
    "Normalizes",
    "Pop",
    "Recommender",
    "bpr",
    "build",
    "distinct",
    "negatives",
    "register",
    "to_ranks",
]
