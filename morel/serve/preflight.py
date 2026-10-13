"""Production startup checks for the serving command."""

from __future__ import annotations

import os
from collections.abc import Mapping

from morel.core.config import Config
from morel.core.errors import Cfg


def validate(
    config: Config,
    *,
    environ: Mapping[str, str] | None = None,
    model_dir: str | None = None,
) -> None:
    """Validate serving configuration before a production socket opens.

    Environment-sensitive credential checks remain in :mod:`morel.serve.auth`;
    this boundary owns configuration and observability invariants. Development
    and test processes retain their permissive defaults.

    Args:
        config: Fully parsed application configuration.
        environ: Optional environment mapping, useful for deterministic tests.
        model_dir: Explicit bundle path supplied by the CLI, when present.

    Raises
    ------
        Cfg: If production mode is enabled with unsafe logging settings.
    """
    config.validate()
    variables = os.environ if environ is None else environ
    if variables.get("MOREL_ENV", "").strip().lower() != "production":
        return
    if not config.log.structured:
        raise Cfg("MOREL_ENV=production requires structured logging")
    if config.log.level.upper() == "DEBUG":
        raise Cfg("MOREL_ENV=production does not allow DEBUG logging")
    inherited = variables.get("MOREL_SERVE_MODEL_DIR", "").strip()
    if not (model_dir or inherited):
        raise Cfg("MOREL_ENV=production requires MOREL_SERVE_MODEL_DIR or --model-dir")


__all__ = ["validate"]
