"""Public API for the morel.complete package."""

import torch.nn as nn

from morel.complete.decoders import Decoders
from morel.complete.protocol import Completer
from morel.core.factory import FactoryRegistry


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


#: Map from config name to completer class for introspection.
KIND: dict[str, type[nn.Module]] = {"mlp": Decoders}
_FACTORIES = FactoryRegistry[nn.Module](
    "completer", KIND, validator=lambda value: isinstance(value, Completer)
)


__all__ = ["KIND", "Completer", "Decoders", "build"]
