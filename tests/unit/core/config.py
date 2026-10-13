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

    def public_aliases(self, tmp_path) -> None:
        """Documented ``from_dict`` and ``from_yaml`` aliases remain usable."""
        config = Config.from_dict({"seed": 7, "device": "cpu"})
        path = tmp_path / "config.yaml"
        config.save(path)
        assert Config.from_yaml(path).hash() == config.hash()

    def rejects(self) -> None:
        with pytest.raises(Cfg):
            Config.parse({"seed": 0, "totally_made_up": True})

    def rejects_nested_unknown(self) -> None:
        """Nested YAML keys must not disappear silently during coercion."""
        with pytest.raises(Cfg, match="unknown Data config key"):
            Config.parse({"data": {"not_a_real_field": True}})

    def rejects_nested_shape(self) -> None:
        """Malformed sections fail as configuration errors, not AttributeError."""
        with pytest.raises(Cfg, match="data section must be a mapping"):
            Config.parse({"data": "not-a-mapping"})

    def env(self, monkeypatch) -> None:
        monkeypatch.setenv("MOREL_SEED", "123")
        c = Config.env()
        assert c.seed == 123

    def serving_bounds(self) -> None:
        """Serving and logging settings fail before a process can start."""
        from morel.core.config import Log, Serve

        with pytest.raises(Cfg, match=r"serve\.port"):
            Config(serve=Serve(port=65_536))
        with pytest.raises(Cfg, match=r"serve\.workers"):
            Config(serve=Serve(workers=0))
        with pytest.raises(Cfg, match=r"log\.level"):
            Config(log=Log(level="verbose"))

    def serving_limits(self) -> None:
        """Serving budgets and proxy policy are validated as configuration."""
        from morel.core.config import Serve

        config = Config(
            serve=Serve(
                rate_limit_per_minute=120,
                admin_limit_per_minute=20,
                factory_timeout=12.5,
                trusted_proxy_cidrs=("10.0.0.0/8",),
                retrieval_max_nodes=2048,
                metrics_path="/internal/metrics",
            )
        )
        assert config.serve.factory_timeout == 12.5
        assert config.serve.retrieval_max_nodes == 2048
        assert config.serve.metrics_path == "/internal/metrics"
        with pytest.raises(Cfg, match=r"serve\.rate_limit_per_minute"):
            Config(serve=Serve(rate_limit_per_minute=0))
        with pytest.raises(Cfg, match=r"serve\.factory_timeout"):
            Config(serve=Serve(factory_timeout=0))
        with pytest.raises(Cfg, match=r"serve\.retrieval_max_nodes"):
            Config(serve=Serve(retrieval_max_nodes=0))
        with pytest.raises(Cfg, match=r"serve\.metrics_path"):
            Config(serve=Serve(metrics_path="metrics"))

    def serving_resource_limits(self) -> None:
        """Operational worker budgets validate without changing artifact identity."""
        from morel.core.config import Serve

        base = Config().hash()
        tuned = Config(
            serve=Serve(
                limit_concurrency=32,
                limit_max_requests=500,
                timeout_keep_alive=2,
                timeout_graceful_shutdown=9,
            )
        )
        assert tuned.hash() == base
        with pytest.raises(Cfg, match=r"serve\.limit_concurrency"):
            Config(serve=Serve(limit_concurrency=0))
        with pytest.raises(Cfg, match=r"serve\.timeout_keep_alive"):
            Config(serve=Serve(timeout_keep_alive=0))

    def schema_bounds(self) -> None:
        """Nested numeric, kind, and string fields fail as domain config errors."""
        import math

        from morel.core.config import Codebook, Completion, Data

        with pytest.raises(Cfg, match=r"data\.min"):
            Config(data=Data(min=-1))
        with pytest.raises(Cfg, match=r"codebook\.size"):
            Config(codebook=Codebook(size=0))
        with pytest.raises(Cfg, match=r"completion\.lr"):
            Config(completion=Completion(lr=math.nan))
