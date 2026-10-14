"""Typed construction and resolution for named extension points."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Generic, TypeVar

from morel.core.errors import Cfg, Error

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
        factory_validator: Optional predicate for the callable contract. It is
            evaluated during registration, so incompatible plugins fail before
            configuration can select them.
    """

    def __init__(
        self,
        name: str,
        factories: Mapping[str, Callable[..., T]],
        *,
        validator: Callable[[object], bool] | None = None,
        factory_validator: Callable[[object], bool] | None = None,
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
        self._factory_validator = factory_validator
        invalid = [
            kind for kind, factory in self._factories.items() if not self._valid_factory(factory)
        ]
        if invalid:
            names = ", ".join(repr(kind) for kind in invalid)
            raise Cfg(f"{name} registry has incompatible factory registration: {names}")

    def _valid_factory(self, factory: Callable[..., T]) -> bool:
        """Validate one factory while sanitizing plugin implementation errors."""
        if self._factory_validator is None:
            return True
        try:
            return bool(self._factory_validator(factory))
        except Exception as exc:
            raise Cfg(f"{self.name} factory contract validation failed") from exc

    def register(self, kind: str, factory: Callable[..., T]) -> None:
        """Register one new factory after validating its extension contract.

        Registration is intentionally additive: replacing a configured name
        could silently change a deployed model, so callers must choose a new
        name or construct a fresh registry.

        Args:
            kind: Stable configuration name for the new implementation.
            factory: Callable matching the registry's construction contract.

        Raises:
            Cfg: If the name is already registered or the factory contract is
                incompatible.
            ValueError: If the name or factory is malformed.
        """
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("factory kind must be a non-empty string")
        if not callable(factory):
            raise ValueError("factory must be callable")
        if kind in self._factories:
            raise Cfg(f"{self.name} factory name already registered: {kind!r}")
        if not self._valid_factory(factory):
            raise Cfg(f"{self.name} registry has incompatible factory registration: {kind!r}")
        self._factories[kind] = factory

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
        try:
            value = self.resolve(kind)(**kwargs)
        except Error:
            raise
        except Exception as exc:
            raise Cfg(f"{self.name} '{kind}' factory failed") from exc
        try:
            valid = self._validator is None or self._validator(value)
        except Exception as exc:
            raise Cfg(f"{self.name} '{kind}' result validation failed") from exc
        if not valid:
            raise Cfg(f"{self.name} '{kind}' does not satisfy its runtime contract")
        return value


__all__ = ["FactoryRegistry"]
