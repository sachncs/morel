"""Public API for the morel.route package."""

from collections.abc import Callable
from types import MappingProxyType

from morel.core.factory import _validate_implementation
from morel.route.router import Dense, Fixed, Gumbel, Router, Top, Weights, build
from morel.route.router import register as _register

#: Internal implementation metadata for the read-only public view.
_KIND: dict[str, type[Router]] = {
    "top": Top,
    "dense": Dense,
    "gumbel": Gumbel,
    "fixed": Fixed,
}
KIND = MappingProxyType(_KIND)


def register(kind: str, factory: Callable[..., Router], *, implementation: type[Router]) -> None:
    """Register an additive router and publish its introspection type."""
    _validate_implementation(implementation, Router, "router")
    _register(kind, factory)
    _KIND[kind] = implementation


__all__ = [
    "KIND",
    "Dense",
    "Fixed",
    "Gumbel",
    "Router",
    "Top",
    "Weights",
    "build",
    "register",
]
