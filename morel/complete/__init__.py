"""Public API for the morel.complete package."""

from collections.abc import Callable
from types import MappingProxyType

import torch.nn as nn

from morel.complete.decoders import Decoders
from morel.complete.protocol import Completer
from morel.core.factory import FactoryRegistry, _accepts_keywords, _validate_implementation


def build(kind: str, *, latent_dim: int, dims: dict[str, int], hidden: int) -> nn.Module:
    """Build the modality completer selected by ``config.complete.kind``.

    Args:
        kind: Completer name. Only ``"mlp"`` is supported.
        latent_dim: Width of the latent representation.
        dims: Mapping from modality name to its feature dimension.
        hidden: Hidden width of each per-modality MLP.

    Returns:
        The constructed completer module.

    Raises:
        ValueError: If ``kind`` is not a known completer name.
    """
    return _FACTORIES.build(kind, latent_dim=latent_dim, dims=dims, hidden=hidden)


#: Internal implementation metadata for the read-only public view.
_KIND: dict[str, type[nn.Module]] = {"mlp": Decoders}
KIND = MappingProxyType(_KIND)
_FACTORIES = FactoryRegistry[nn.Module](
    "completer",
    _KIND,
    validator=lambda value: isinstance(value, Completer),
    factory_validator=lambda value: _accepts_keywords(value, ("latent_dim", "dims", "hidden")),
)


def register(
    kind: str, factory: Callable[..., nn.Module], *, implementation: type[nn.Module]
) -> None:
    """Register an additive completer implementation under a new config name."""
    _validate_implementation(implementation, Completer, "completer")
    _FACTORIES.register(kind, factory)
    _KIND[kind] = implementation


__all__ = ["KIND", "Completer", "Decoders", "build", "register"]
