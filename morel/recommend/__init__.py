"""Public API for the morel.recommend package."""

import torch.nn as nn

from morel.core.errors import Cfg
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

    Returns
    -------
        The constructed ranker module.

    Raises
    ------
        ValueError: If ``kind`` is not a known ranker name.
    """
    if kind == "light":
        ranker: nn.Module = Light(
            users=users,
            items=items,
            embed=embed,
            layers=layers,
            feature_dim=feature_dim,
            seed=seed,
        )
    elif kind == "mf":
        ranker = MF(users=users, items=items, embed=embed, seed=seed)
    elif kind == "pop":
        ranker = Pop(users=users, items=items)
    else:
        raise Cfg(f"unknown recommender '{kind}'; available: light, mf, pop")
    if not isinstance(ranker, Recommender):
        raise Cfg(f"recommender '{kind}' does not satisfy the Recommender contract")
    return ranker


#: Map from config name to ranker class for introspection.
KIND: dict[str, type[nn.Module]] = {
    "light": Light,
    "mf": MF,
    "pop": Pop,
}


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
    "to_ranks",
]
