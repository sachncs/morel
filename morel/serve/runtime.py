"""Importable application factory for multi-worker Uvicorn deployments."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from morel.core.config import Config
from morel.core.errors import Cfg, Model
from morel.serve import Loader, create
from morel.serve.factory import from_run
from morel.serve.preflight import validate as validate_preflight
from morel.serve.protocol import is_serving_pipeline


def create_app() -> FastAPI:
    """Create a worker-local app from the inherited serving environment.

    Uvicorn requires an importable application factory when ``workers > 1``.
    The CLI validates the bundle in the parent process before starting; each
    worker repeats the validation and eagerly materializes its own model so a
    bad worker cannot advertise readiness.
    """
    config = Config.env()
    model_dir = os.environ.get("MOREL_SERVE_MODEL_DIR", "").strip()
    validate_preflight(config, model_dir=model_dir)
    loader = Loader(factory_timeout=config.serve.factory_timeout)
    if model_dir:
        root = Path(model_dir)
        loader.register("default", lambda: from_run(root), validator=is_serving_pipeline)
        try:
            pipeline = loader.get("default")
        except Model as exc:
            raise Cfg("serving model factory returned an incompatible pipeline contract") from exc
        if not is_serving_pipeline(pipeline):
            raise Cfg("serving model factory returned an incompatible pipeline contract")
    return create(
        loader,
        rate_limit_per_minute=config.serve.rate_limit_per_minute,
        admin_limit_per_minute=config.serve.admin_limit_per_minute,
        trusted_proxy_cidrs=tuple(config.serve.trusted_proxy_cidrs),
        metrics_enabled=config.serve.metrics_enabled,
        metrics_path=config.serve.metrics_path,
    )


__all__ = ["create_app"]
