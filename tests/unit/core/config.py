"""Tests for morel.core.config."""

from __future__ import annotations

import pytest

from morel.core.config import Config
from morel.core.errors import Cfg


class Checker:
    """Aggregated test methods for this module."""

    def default(self) -> None:
        c = Config()
        c.validate()

    def stable(self) -> None:
        a = Config().hash()
        b = Config().hash()
        assert a == b

    def changes(self) -> None:
        a = Config()
        b = Config(seed=43)
        assert a.hash() != b.hash()

    def invalid(self) -> None:
        with pytest.raises(Cfg):
            Config(seed=-1).validate()

    def mask(self) -> None:
        """``Config(...)`` rejects out-of-range masking ratios at construction."""
        from morel.core.config import Masking

        bad = Masking(ratio=2.0)
        with pytest.raises(Cfg):
            Config(masking=bad)

    def mask_validate_only(self) -> None:
        """``Config(...)`` with valid bounds passes __post_init__."""
        c = Config()
        assert c.validate() is None

    def to(self, tmp_path) -> None:
        c = Config()
        path = tmp_path / "config.yaml"
        c.save(path)
        loaded = Config.load(path)
        assert loaded.hash() == c.hash()

    def rejects(self) -> None:
        with pytest.raises(Cfg):
            Config.parse({"seed": 0, "totally_made_up": True})

    def env(self, monkeypatch) -> None:
        monkeypatch.setenv("MOREL_SEED", "123")
        c = Config.env()
        assert c.seed == 123
