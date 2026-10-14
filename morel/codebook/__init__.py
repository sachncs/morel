"""Public API for the morel.codebook package."""

from collections.abc import Callable
from types import MappingProxyType

from morel.codebook.codebook import (
    VQ,
    Codebook,
    Noop,
    Soft,
    balance,
    usage,
)
from morel.core.factory import FactoryRegistry, _accepts_keywords, _validate_implementation
from morel.route import Router


def build(
    kind: str,
    *,
    dim: int,
    size: int,
    router: Router,
    seed: int | None = None,
) -> Codebook:
    """Build the codebook selected by ``config.codebook.kind``.

    Args:
        kind: Codebook name. One of ``"gumbel"``, ``"vq"``, ``"identity"``.
        dim: Embedding dimension.
        size: Number of codebook entries.
        router: Router used by Gumbel-VQ to produce assignment weights.
        seed: Optional RNG seed for reproducibility.

    Returns:
        The constructed codebook.

    Raises:
        ValueError: If ``kind`` is not a known codebook name.
    """
    return _FACTORIES.build(kind, dim=dim, size=size, router=router, seed=seed)


#: Internal implementation metadata for the read-only public view.
_KIND: dict[str, type[Codebook]] = {
    "gumbel": Soft,
    "vq": VQ,
    "identity": Noop,
}
KIND = MappingProxyType(_KIND)


def register(
    kind: str, factory: Callable[..., Codebook], *, implementation: type[Codebook]
) -> None:
    """Register an additive codebook implementation under a new config name."""
    _validate_implementation(implementation, Codebook, "codebook")
    _FACTORIES.register(kind, factory)
    _KIND[kind] = implementation


def _build_soft(*, dim: int, size: int, router: Router, seed: int | None) -> Codebook:
    """Adapt the shared constructor shape to the Gumbel codebook."""
    return Soft(dim=dim, size=size, router=router, seed=seed)


def _build_vq(*, dim: int, size: int, router: Router, seed: int | None) -> Codebook:
    """Adapt the shared constructor shape to vector quantization."""
    del router
    return VQ(dim=dim, size=size, seed=seed)


def _build_noop(*, dim: int, size: int, router: Router, seed: int | None) -> Codebook:
    """Adapt the shared constructor shape to the identity codebook."""
    del router, seed
    return Noop(dim=dim, size=size)


_FACTORIES = FactoryRegistry[Codebook](
    "codebook",
    {"gumbel": _build_soft, "vq": _build_vq, "identity": _build_noop},
    validator=lambda value: isinstance(value, Codebook),
    factory_validator=lambda value: _accepts_keywords(value, ("dim", "size", "router", "seed")),
)


__all__ = [
    "KIND",
    "VQ",
    "Codebook",
    "Noop",
    "Soft",
    "balance",
    "build",
    "register",
    "usage",
]
