"""Tests for typed extension-point factories."""

from __future__ import annotations

import pytest

from morel.core.errors import Cfg
from morel.core.factory import FactoryRegistry, _accepts_keywords


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

    def validator_failure_is_typed(self) -> None:
        """A broken plugin validator cannot leak backend details."""

        def broken(_: object) -> bool:
            raise RuntimeError("plugin secret")

        with pytest.raises(Cfg, match="factory contract validation failed") as caught:
            FactoryRegistry[int]("number", {"one": lambda: 1}, factory_validator=broken)
        assert "plugin secret" not in str(caught.value)

    def factory_failure_is_typed(self) -> None:
        """A plugin constructor failure becomes a stable configuration error."""

        def broken() -> int:
            raise RuntimeError("backend secret")

        registry = FactoryRegistry[int]("number", {"broken": broken})
        with pytest.raises(Cfg, match="factory failed") as caught:
            registry.build("broken")
        assert "backend secret" not in str(caught.value)

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

    def registration(self) -> None:
        """External factories can register without replacing a live name."""
        registry = FactoryRegistry[int](
            "number",
            {"one": lambda: 1},
            factory_validator=callable,
        )
        registry.register("two", lambda: 2)
        assert registry.build("two") == 2
        with pytest.raises(Cfg, match="already registered"):
            registry.register("one", lambda: 3)

    def registration_contract(self) -> None:
        """Incompatible external factories are rejected before publication."""

        def valid() -> int:
            return 1

        valid.plugin_ok = True  # type: ignore[attr-defined]
        registry = FactoryRegistry[int](
            "number",
            {"one": valid},
            factory_validator=lambda value: getattr(value, "plugin_ok", False),
        )

        def broken() -> int:
            return 2

        with pytest.raises(Cfg, match="incompatible factory registration"):
            registry.register("broken", broken)
        assert "broken" not in registry

    def keyword_contract(self) -> None:
        """Keyword-based extension points reject incompatible call shapes."""

        def explicit(*, dims: object, hidden: object) -> None:
            del dims, hidden

        def variadic(**kwargs: object) -> None:
            del kwargs

        def missing(*, dims: object) -> None:
            del dims

        def positional_only(dims: object, /, hidden: object) -> None:
            del dims, hidden

        assert _accepts_keywords(explicit, ("dims", "hidden"))
        assert _accepts_keywords(variadic, ("dims", "hidden"))
        assert not _accepts_keywords(missing, ("dims", "hidden"))
        assert not _accepts_keywords(positional_only, ("dims", "hidden"))
