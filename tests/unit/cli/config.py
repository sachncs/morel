"""The CLI must read the configuration rather than hardcoding its behaviour.

``configure_log`` was called with a fixed level, the eval commands used
hardcoded cutoffs and mask ratios, and ``morel serve`` had its own host and
port defaults. Every one of those config fields was inert.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from morel.cli import eval, setup_log
from morel.core.config import Config


def write(tmp_path: Path, **payload: Any) -> Path:
    """Write a config YAML and return its path."""
    path = tmp_path / "config.yaml"
    Config.parse(payload).save(path)
    return path


class Checker:
    """Aggregated test methods for this module."""

    def rank(self, tmp_path: Path, capsys: Any) -> None:
        path = write(tmp_path, eval={"ks": [3, 7]})
        assert eval(["rank", "--config", str(path)]) == 0

        out = capsys.readouterr().out
        assert "recall@3=" in out
        assert "recall@7=" in out
        assert "recall@10=" not in out, "the hardcoded k=10 must be gone"

    def robustness(self, tmp_path: Path, capsys: Any) -> None:
        path = write(tmp_path, eval={"robustness": [0.2, 0.8]})
        assert eval(["robustness", "--config", str(path)]) == 0
        out = capsys.readouterr().out
        assert "0.2" in out
        assert "0.8" in out
        assert "0.7" not in out, "the hardcoded ratio list must be gone"

    def defaults(self, capsys: Any) -> None:
        assert eval(["rank"]) == 0
        out = capsys.readouterr().out
        for k in Config().eval.ks:
            assert f"recall@{k}=" in out

    def logging(self, tmp_path: Path) -> None:
        import logging

        path = write(tmp_path, log={"level": "ERROR", "structured": True})
        setup_log(["--config", str(path)])
        assert logging.getLogger("morel").level == logging.ERROR

        setup_log([])
        assert logging.getLogger("morel").level == logging.getLevelName(Config().log.level)

    def survives(self, tmp_path: Path) -> None:
        """The logger must come up so the user can be told the config is broken."""
        import logging

        bad = tmp_path / "bad.yaml"
        bad.write_text("{not: valid: yaml", encoding="utf-8")
        setup_log(["--config", str(bad)])
        assert logging.getLogger("morel").level == logging.INFO

    def serve(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "morel", "serve", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        for flag in ("--host", "--port", "--workers"):
            assert flag in result.stdout, f"{flag} missing from serve --help"
        assert "serve.host" in result.stdout

    def uses(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        class Fake:
            @staticmethod
            def run(app: Any, **kwargs: Any) -> None:
                captured["app"] = app
                captured.update(kwargs)

        monkeypatch.setitem(sys.modules, "uvicorn", Fake)
        path = write(tmp_path, serve={"host": "127.0.0.1", "port": 9111, "workers": 3})

        from morel.cli import api

        assert api(["--config", str(path)]) == 0
        assert captured["host"] == "127.0.0.1"
        assert captured["port"] == 9111
        assert captured["workers"] == 3
        assert captured["app"] == "morel.serve.runtime:create_app"
        assert captured["factory"] is True

    def flags(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        class Fake:
            @staticmethod
            def run(app: Any, **kwargs: Any) -> None:
                captured.update(kwargs)

        monkeypatch.setitem(sys.modules, "uvicorn", Fake)
        path = write(tmp_path, serve={"host": "127.0.0.1", "port": 9111})

        from morel.cli import api

        assert api(["--config", str(path), "--port", "1234"]) == 0
        assert captured["host"] == "127.0.0.1", "unspecified flags still come from config"
        assert captured["port"] == 1234, "an explicit flag must win"

    def eager_model_validation(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Serving validates a model bundle before handing control to Uvicorn."""
        calls: list[Path] = []
        captured: dict[str, Any] = {}

        class Fake:
            @staticmethod
            def run(app: Any, **kwargs: Any) -> None:
                captured.update(kwargs)

        def fake_from_run(path: Path) -> object:
            calls.append(path)
            return object()

        monkeypatch.setitem(sys.modules, "uvicorn", Fake)
        monkeypatch.setattr("morel.serve.factory.from_run", fake_from_run)
        model_dir = tmp_path / "run"

        from morel.cli import api
        from morel.core.errors import Cfg

        with pytest.raises(Cfg, match="incompatible pipeline contract"):
            api(["--model-dir", str(model_dir)])
        assert calls == [model_dir]
        assert captured == {}

    def production_auth_precedes_model_load(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid production credentials fail before expensive model loading."""
        monkeypatch.setenv("MOREL_ENV", "production")
        for name in ("MOREL_AUTH_TOKEN", "MOREL_AUTH_TOKEN_READ", "MOREL_AUTH_TOKEN_ADMIN"):
            monkeypatch.delenv(name, raising=False)
        calls: list[Path] = []

        def fake_from_run(path: Path) -> object:
            calls.append(path)
            return object()

        monkeypatch.setattr("morel.serve.factory.from_run", fake_from_run)
        from morel.cli import api
        from morel.core.errors import Cfg

        with pytest.raises(Cfg, match="MOREL_ENV=production"):
            api(["--model-dir", str(tmp_path / "run")])
        assert calls == []
