"""Public API for the morel.encode package."""

from collections.abc import Callable
from types import MappingProxyType

import torch.nn as nn

from morel.core.factory import FactoryRegistry, _accepts_keywords, _validate_implementation
from morel.encode.baseline import Baseline, Enc, GraphEncoder, Identity, Sum
from morel.encode.input import Input
from morel.encode.layer import Layer
from morel.encode.pool import CLS, Attention, Mean, Token
from morel.encode.transformer import Transformer


def build(
    kind: str,
    *,
    dims: dict[str, int],
    pe_dim: int,
    hidden: int,
    layers: int,
    heads: int,
    dropout: float,
) -> nn.Module:
    """Build the joint encoder selected by ``config.encode.kind``.

    Args:
        kind: Encoder name. One of ``"transformer"`` or ``"identity"``.
        dims: Mapping from modality name to its feature dimension.
        pe_dim: Positional-encoding dimension.
        hidden: Hidden width of the encoder output.
        layers: Number of transformer layers (ignored for ``identity``).
        heads: Number of attention heads (ignored for ``identity``).
        dropout: Dropout rate (ignored for ``identity``).

    Returns:
        The constructed encoder module.

    Raises:
        ValueError: If ``kind`` is not a known encoder name.
    """
    return _FACTORIES.build(
        kind,
        dims=dims,
        pe_dim=pe_dim,
        hidden=hidden,
        layers=layers,
        heads=heads,
        dropout=dropout,
    )


#: Internal implementation metadata for the read-only public view.
_KIND: dict[str, type[nn.Module]] = {
    "transformer": Transformer,
    "identity": Identity,
}
KIND = MappingProxyType(_KIND)


def register(
    kind: str, factory: Callable[..., nn.Module], *, implementation: type[nn.Module]
) -> None:
    """Register an additive encoder implementation under a new config name."""
    _validate_implementation(implementation, GraphEncoder, "encoder")
    _FACTORIES.register(kind, factory)
    _KIND[kind] = implementation


def _build_transformer(
    *,
    dims: dict[str, int],
    pe_dim: int,
    hidden: int,
    layers: int,
    heads: int,
    dropout: float,
) -> nn.Module:
    """Adapt the shared constructor shape to the transformer implementation."""
    return Transformer(
        dims=dims,
        pe_dim=pe_dim,
        hidden=hidden,
        layers=layers,
        heads=heads,
        dropout=dropout,
    )


def _build_identity(
    *,
    dims: dict[str, int],
    pe_dim: int,
    hidden: int,
    layers: int,
    heads: int,
    dropout: float,
) -> nn.Module:
    """Adapt the shared constructor shape to the identity implementation."""
    del layers, heads, dropout
    return Identity(dims, pe_dim, hidden)


_FACTORIES = FactoryRegistry[nn.Module](
    "encoder",
    {"transformer": _build_transformer, "identity": _build_identity},
    validator=lambda value: isinstance(value, GraphEncoder),
    factory_validator=lambda value: _accepts_keywords(
        value, ("dims", "pe_dim", "hidden", "layers", "heads", "dropout")
    ),
)


__all__ = [
    "CLS",
    "KIND",
    "Attention",
    "Baseline",
    "Enc",
    "GraphEncoder",
    "Identity",
    "Input",
    "Layer",
    "Mean",
    "Sum",
    "Token",
    "Transformer",
    "build",
    "register",
]
