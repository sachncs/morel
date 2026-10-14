"""Tests for typed extension-point factories."""

from __future__ import annotations

import pytest

from morel.core.errors import Cfg
from morel.core.factory import FactoryRegistry


class Checker:
    """Aggregated tests for ``FactoryRegistry``."""

    def registry(self) -> None:
        """The registry resolves a named factory and returns its value."""
        registry = FactoryRegistry[int]("number", {"one": lambda: 1})
        assert registry.build("one") == 1
        assert registry.keys() == ("one",)
        assert "one" in registry

    def unknown(self) -> None:
        """Unknown extension names fail with a typed configuration error."""
        registry = FactoryRegistry[int]("number", {"one": lambda: 1})
        with pytest.raises(Cfg, match="unknown number 'missing'"):
            registry.build("missing")

    def validates(self) -> None:
        """Factories cannot bypass the declared runtime contract."""
        registry = FactoryRegistry[int](
            "number", {"bad": lambda: "wrong"}, validator=lambda v: isinstance(v, int)
        )
        with pytest.raises(Cfg, match="runtime contract"):
            registry.build("bad")

    def validates_factory(self) -> None:
        """Registries reject incompatible factories during registration."""
        with pytest.raises(Cfg, match="incompatible factory registration"):
            FactoryRegistry[int](
                "number",
                {"bad": lambda: 1},
                factory_validator=lambda value: callable(value) and hasattr(value, "required"),
            )

    def snapshots(self) -> None:
        """Mutating the source mapping does not mutate the registry."""
        factories = {"one": lambda: 1}
        registry = FactoryRegistry[int]("number", factories)
        factories["two"] = lambda: 2
        assert registry.keys() == ("one",)

    def rejects_invalid_definition(self) -> None:
        """Empty registries and names are rejected at composition time."""
        with pytest.raises(ValueError, match="must not be empty"):
            FactoryRegistry[int]("number", {})
        with pytest.raises(ValueError, match="name must be non-empty"):
            FactoryRegistry[int]("", {"one": lambda: 1})
