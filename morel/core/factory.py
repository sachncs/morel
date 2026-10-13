"""Typed construction and resolution for named extension points."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Generic, TypeVar

from morel.core.errors import Cfg

T = TypeVar("T")


class FactoryRegistry(Generic[T]):
    """Resolve named factories and validate their runtime contract.

    The registry keeps configuration-facing names separate from construction
    logic. Callers may expose the original mapping for introspection while
    using this class at the composition boundary to validate every result.

    Args:
        name: Human-readable extension-point name used in configuration errors.
        factories: Mapping from stable configuration names to callables.
        validator: Optional runtime contract predicate for constructed values.
    """

    def __init__(
        self,
        name: str,
        factories: Mapping[str, Callable[..., T]],
        *,
        validator: Callable[[object], bool] | None = None,
    ) -> None:
        """Create a validated registry without exposing mutable internals."""
        if not name.strip():
            raise ValueError("registry name must be non-empty")
        if not factories:
            raise ValueError(f"{name} registry must not be empty")
        if any(not isinstance(key, str) or not key for key in factories):
            raise ValueError(f"{name} registry keys must be non-empty strings")
        if any(not callable(factory) for factory in factories.values()):
            raise ValueError(f"{name} registry values must be callable")
        self.name = name
        self._factories = dict(factories)
        self._validator = validator

    def __contains__(self, kind: object) -> bool:
        """Return whether ``kind`` is registered."""
        return kind in self._factories

    def __iter__(self) -> Iterable[str]:
        """Iterate over registered configuration names."""
        return iter(self._factories)

    def keys(self) -> tuple[str, ...]:
        """Return registered names in declaration order."""
        return tuple(self._factories)

    def resolve(self, kind: str) -> Callable[..., T]:
        """Return a registered factory or raise a typed configuration error."""
        factory = self._factories.get(kind)
        if factory is None:
            available = ", ".join(self.keys()) or "(none)"
            raise Cfg(f"unknown {self.name} '{kind}'; available: {available}")
        return factory

    def build(self, kind: str, **kwargs: object) -> T:
        """Construct and validate one named component."""
        value = self.resolve(kind)(**kwargs)
        if self._validator is not None and not self._validator(value):
            raise Cfg(f"{self.name} '{kind}' does not satisfy its runtime contract")
        return value


__all__ = ["FactoryRegistry"]
