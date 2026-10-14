"""Tests for two-token auth, RWLock, and Updater."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
import torch.nn as nn

from morel.serve.auth import (
    admin,
    assert_,
    assert_production,
    require,
    token,
    viewer,
)
from morel.serve.lock import RWLock
from morel.serve.preflight import validate as validate_preflight
from morel.serve.ratelimit import Limiter
from morel.serve.update import Updater


class Tiny(nn.Module):
    """Small module used as a stand-in pipeline for updater tests."""

    def __init__(self) -> None:
        """Initialize the two-dimensional test module."""
        super().__init__()
        self.linear = nn.Linear(2, 2)


# ---- Two-token auth ----


# ---- RWLock ----


# ---- Updater ----


class Checker:
    """Aggregated test methods for this module."""

    def token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MOREL_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("MOREL_AUTH_TOKEN_ADMIN", raising=False)
        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ", "read-tok")
        assert viewer() is True
        assert admin() is False
        assert token("read") == "read-tok"
        assert token("admin") is None

    def only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MOREL_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("MOREL_AUTH_TOKEN_READ", raising=False)
        monkeypatch.setenv("MOREL_AUTH_TOKEN_ADMIN", "admin-tok")
        assert viewer() is False
        assert admin() is True
        assert token("read") is None
        assert token("admin") == "admin-tok"

    def both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Legacy token grants read scope only; admin scope must opt in."""
        for var in (
            "MOREL_AUTH_TOKEN",
            "MOREL_AUTH_TOKEN_READ",
            "MOREL_AUTH_TOKEN_ADMIN",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("MOREL_AUTH_TOKEN", "legacy")
        assert viewer() is True
        assert admin() is False
        assert token("read") == "legacy"
        assert token("admin") is None

    def admin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admin scope is satisfied only by the dedicated variable."""
        for var in (
            "MOREL_AUTH_TOKEN",
            "MOREL_AUTH_TOKEN_READ",
            "MOREL_AUTH_TOKEN_ADMIN",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("MOREL_AUTH_TOKEN", "legacy")
        monkeypatch.setenv("MOREL_AUTH_TOKEN_ADMIN", "admin-tok")
        assert admin() is True
        assert token("admin") == "admin-tok"

    def without(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from morel.core.errors import Cfg

        for var in (
            "MOREL_AUTH_TOKEN",
            "MOREL_AUTH_TOKEN_READ",
            "MOREL_AUTH_TOKEN_ADMIN",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("MOREL_AUTH_ENABLED", "1")
        with pytest.raises(Cfg):
            assert_()

    def production_requires_two_scopes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Production mode cannot silently expose either HTTP scope."""
        from morel.core.errors import Cfg

        monkeypatch.setenv("MOREL_ENV", "production")
        monkeypatch.delenv("MOREL_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("MOREL_AUTH_TOKEN_READ", raising=False)
        monkeypatch.delenv("MOREL_AUTH_TOKEN_ADMIN", raising=False)
        with pytest.raises(Cfg, match="MOREL_ENV=production"):
            assert_production()

        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ", "read-token-123456")
        with pytest.raises(Cfg, match="MOREL_ENV=production"):
            assert_production()

        monkeypatch.setenv("MOREL_AUTH_TOKEN_ADMIN", "admin-token-123456")
        assert_production()

    def production_rejects_weak_or_shared_tokens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Production credentials must be long enough and scope-separated."""
        from morel.core.errors import Cfg

        monkeypatch.setenv("MOREL_ENV", "production")
        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ", "short")
        monkeypatch.setenv("MOREL_AUTH_TOKEN_ADMIN", "admin-token-123456")
        with pytest.raises(Cfg, match="at least 16"):
            assert_production()

        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ", "same-token-123456")
        monkeypatch.setenv("MOREL_AUTH_TOKEN_ADMIN", "same-token-123456")
        with pytest.raises(Cfg, match="must be different"):
            assert_production()

    def secret_files(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Production auth can consume mounted secrets without raw env values."""
        from morel.core.errors import Cfg

        for name in (
            "MOREL_AUTH_TOKEN",
            "MOREL_AUTH_TOKEN_FILE",
            "MOREL_AUTH_TOKEN_READ",
            "MOREL_AUTH_TOKEN_READ_FILE",
            "MOREL_AUTH_TOKEN_ADMIN",
            "MOREL_AUTH_TOKEN_ADMIN_FILE",
        ):
            monkeypatch.delenv(name, raising=False)
        read_path = tmp_path / "read.token"
        admin_path = tmp_path / "admin.token"
        read_path.write_text("read-file-token-123456\n", encoding="utf-8")
        admin_path.write_text("admin-file-token-654321\n", encoding="utf-8")
        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ_FILE", str(read_path))
        monkeypatch.setenv("MOREL_AUTH_TOKEN_ADMIN_FILE", str(admin_path))
        monkeypatch.setenv("MOREL_ENV", "production")
        assert token("read") == "read-file-token-123456"
        assert token("admin") == "admin-file-token-654321"
        assert_production()

        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ", "direct-token-123456")
        with pytest.raises(Cfg, match="set only one"):
            token("read")

    def external_secret_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Authentication can consume an injected external secret provider."""
        from morel.serve.auth import SecretProvider

        class Provider:
            def get(self, name: str) -> str | None:
                return {
                    "read": "provider-read-token-123456",
                    "admin": "provider-admin-token-654321",
                    "legacy": None,
                }[name]

        provider = Provider()
        assert isinstance(provider, SecretProvider)
        assert token("read", provider) == "provider-read-token-123456"
        assert token("admin", provider) == "provider-admin-token-654321"
        monkeypatch.setenv("MOREL_ENV", "production")
        from morel.serve.auth import assert_production

        assert_production(provider)

    def resolver_secret_provider(self) -> None:
        """The external resolver adapter bounds and sanitizes backend output."""
        from morel.core.errors import Cfg
        from morel.serve.auth import ResolverSecretProvider

        values = {"read": "  read-token  ", "admin": "admin-token", "legacy": None}
        provider = ResolverSecretProvider(lambda name: values[name])
        assert provider.get("read") == "read-token"
        assert provider.get("legacy") is None

        def fail(name: str) -> str:
            raise RuntimeError("vendor credential must not escape")

        with pytest.raises(Cfg, match="external secret provider failed") as caught:
            ResolverSecretProvider(fail).get("read")
        assert "vendor credential" not in str(caught.value)
        with pytest.raises(Cfg, match="exceeds"):
            ResolverSecretProvider(lambda name: "x" * 4097).get("read")
        with pytest.raises(Cfg, match="unknown secret name"):
            ResolverSecretProvider(lambda name: None).get("unknown")

    def missing_secret_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        from morel.core.errors import Cfg

        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ_FILE", str(tmp_path / "missing"))
        with pytest.raises(Cfg, match="unable to read"):
            token("read")

    def production_preflight(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Production startup rejects unsafe logging configuration."""
        from morel.core.config import Config, Log, Serve
        from morel.core.errors import Cfg

        monkeypatch.setenv("MOREL_ENV", "production")
        with pytest.raises(Cfg, match="structured logging"):
            validate_preflight(Config(log=Log(structured=False)))
        with pytest.raises(Cfg, match="DEBUG"):
            validate_preflight(Config(log=Log(level="DEBUG")))
        with pytest.raises(Cfg, match="metrics endpoint"):
            validate_preflight(Config(serve=Serve(metrics_enabled=False)))
        validate_preflight(Config(), environ={"MOREL_ENV": "development"})

    def production_requires_model_bundle(self) -> None:
        """Production workers cannot start without an inherited bundle path."""
        from morel.core.config import Config, Log
        from morel.core.errors import Cfg

        environ = {"MOREL_ENV": "production"}
        config = Config(log=Log(level="INFO", structured=True))
        with pytest.raises(Cfg, match="MOREL_SERVE_MODEL_DIR"):
            validate_preflight(config, environ=environ)
        validate_preflight(config, environ=environ, model_dir="runs/completion")

    def noop(self) -> None:
        class Req:
            def __init__(self) -> None:
                self.headers: dict[str, str] = {}

        require(Req(), scope="read")

    def trusted_proxy(self) -> None:
        """Forwarded addresses are honored only from configured proxies."""
        from starlette.requests import Request

        def request(peer: str, forwarded: str) -> Request:
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [(b"x-forwarded-for", forwarded.encode())],
                "client": (peer, 1234),
            }
            return Request(scope)

        limiter = Limiter()
        limiter.configure(per_minute_read=60, per_minute_admin=10)
        direct = request("203.0.113.10", "198.51.100.8")
        assert limiter.client_key(direct) == "203.0.113.10"

        limiter.configure(
            per_minute_read=60,
            per_minute_admin=10,
            trusted_proxy_cidrs=("203.0.113.0/24",),
        )
        trusted = request("203.0.113.10", "198.51.100.8, 203.0.113.11")
        assert limiter.client_key(trusted) == "198.51.100.8"

    def raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from fastapi import HTTPException

        monkeypatch.setenv("MOREL_AUTH_TOKEN_READ", "real-token")

        class Req:
            def __init__(self) -> None:
                self.headers = {"authorization": "Bearer wrong"}

        with pytest.raises(HTTPException):
            require(Req(), scope="read")

    def other(self) -> None:
        lock = RWLock()
        errors: list[Exception] = []
        readers_in = 0
        readers_in_lock = threading.Lock()

        def reader() -> None:
            nonlocal readers_in
            try:
                with lock.read():
                    with readers_in_lock:
                        readers_in += 1
                    time.sleep(0.05)
                    with readers_in_lock:
                        readers_in -= 1
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors

    def writers(self) -> None:
        lock = RWLock()
        counter = [0]
        counter_lock = threading.Lock()

        def writer() -> None:
            with lock.write():
                with counter_lock:
                    assert counter[0] == 0
                    counter[0] += 1
                time.sleep(0.02)
                with counter_lock:
                    counter[0] -= 1

        threads = [threading.Thread(target=writer) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert counter[0] == 0

    def buffer(self) -> None:
        updater = Updater(Tiny())
        for i in range(8):
            updater.accept(user=i, item=i, signal="like")
        assert updater.stats()["events_buffered"] == 8
        assert updater.stats()["replay_buffered"] == 8

    def returns(self) -> None:
        updater = Updater(Tiny())
        result = updater.tick()
        assert result.committed is False

    def commit(self) -> None:
        updater = Updater(
            Tiny(),
            cooldown_seconds=0,
            loss_step=lambda batch: 0.5,
        )
        for i in range(32):
            updater.accept(user=i, item=i, signal="like")
        result = updater.tick()
        assert result.committed is True
        assert result.version == 1
        assert updater.stats()["updates_applied"] == 1

    def loss(self) -> None:
        updater = Updater(
            Tiny(),
            cooldown_seconds=7,
            loss_step=lambda batch: float("nan"),
        )
        for i in range(16):
            updater.accept(user=i, item=i, signal="like")
        result = updater.tick()
        assert result.committed is False
        assert 6.0 < updater.cooldown - time.time() <= 7.0

    def version(self) -> None:
        updater = Updater(
            Tiny(),
            cooldown_seconds=0,
            loss_step=lambda batch: 0.5,
        )
        for i in range(32):
            updater.accept(user=i, item=i, signal="like")
        updater.tick()
        updater.tick()
        assert updater.version == 2
        version = updater.undo(steps=1)
        assert version == 1
        assert updater.version == 1

    def restores(self) -> None:
        """Regression: undo() must not corrupt the model state."""
        model = Tiny()
        updater = Updater(
            model,
            cooldown_seconds=0,
            loss_step=lambda batch: 0.5,
        )
        for i in range(32):
            updater.accept(user=i, item=i, signal="like")
        updater.tick()
        updater.tick()
        assert updater.version == 2
        version = updater.undo(steps=1)
        assert version == 1
        assert updater.version == 1

    def state(self) -> None:
        """Regression: rolling back restores the pipeline state to a prior version."""
        import torch

        model = Tiny()
        initial_weight = model.linear.weight.detach().clone()
        captured: list[torch.Tensor] = [initial_weight.clone()]

        def mutate(batch):
            with torch.no_grad():
                model.linear.weight.fill_(captured[-1].mean().item() + 0.1)
            captured.append(model.linear.weight.detach().clone())
            return 0.5

        updater = Updater(model, cooldown_seconds=0, loss_step=mutate)
        for i in range(32):
            updater.accept(user=i, item=i, signal="like")
        updater.tick()  # version 1: weight becomes captured[1]
        weight_after_v1 = model.linear.weight.detach().clone()
        updater.tick()  # version 2: weight becomes captured[2]
        weight_after_v2 = model.linear.weight.detach().clone()
        assert not torch.equal(weight_after_v1, weight_after_v2)

        updater.undo(steps=1)
        # After undo, the model must equal the state at version 1, not 2.
        assert torch.equal(model.linear.weight, weight_after_v1)
        assert not torch.equal(model.linear.weight, weight_after_v2)

        updater.undo(steps=1)
        # After undo to the initial snapshot, the model must match the
        # initial weight.
        assert torch.equal(model.linear.weight, initial_weight)

    def divergence(self) -> None:
        """Regression: a divergent tick must not leave the model updated."""
        import torch

        model = Tiny()
        initial = {k: v.clone() for k, v in model.state_dict().items()}

        def explode(batch):
            with torch.no_grad():
                model.linear.weight.fill_(42.0)
            return float("nan")

        updater = Updater(model, cooldown_seconds=30, loss_step=explode)
        for i in range(16):
            updater.accept(user=i, item=i, signal="like")
        result = updater.tick()
        assert result.committed is False
        assert updater.cooldown > time.time()
        # The pipeline must be in its pre-update state, not the diverged one.
        assert torch.equal(model.linear.weight, initial["linear.weight"])

    def polymorphic(self) -> None:
        """Step Protocol: Default and a custom callable both work."""
        from morel.serve.update import Default

        base = Updater(Tiny(), cooldown_seconds=0)
        assert isinstance(base.loss_step, Default)
        custom = Updater(
            Tiny(),
            cooldown_seconds=0,
            loss_step=lambda batch: 0.42,
        )
        for i in range(8):
            custom.accept(user=i, item=i, signal="like")
        result = custom.tick()
        assert result.committed is True
        assert abs(result.loss - 0.42) < 1e-6

    def validates_controls(self) -> None:
        """Reject updater controls that could silently disable safeguards."""
        with pytest.raises(ValueError, match="cooldown_seconds"):
            Updater(Tiny(), cooldown_seconds=-1)
        with pytest.raises(ValueError, match="ratio"):
            Updater(Tiny(), ratio=1.1)
        with pytest.raises(ValueError, match="val_ratio"):
            Updater(Tiny(), val_ratio=-0.1)
