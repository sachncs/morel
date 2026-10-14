"""FastAPI app factory for morel inference."""

from __future__ import annotations

import logging
import math
import os
import uuid
from typing import TYPE_CHECKING, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi import Query as FastAPIQuery
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from morel import __version__
from morel.core.errors import Error
from morel.serve import auth
from morel.serve.loader import Loader
from morel.serve.metrics import Registry, metrics_response
from morel.serve.observe import ObserveMiddleware
from morel.serve.protocol import ServingPipeline, is_serving_pipeline
from morel.serve.ratelimit import Limiter, ratelimit_dependency
from morel.serve.schema import (
    MAX_ITEMS_PER_REQUEST,
    MAX_ROLLBACK_STEPS,
    Done,
    Fill,
    Health,
    List,
    Pick,
    Query,
    serialize,
)

# FastAPI's decorator typing varies across the supported Python/dependency
# matrix; the handler bodies remain strictly checked below.
# mypy: disable-error-code=unused-ignore
log = logging.getLogger("morel.serve.app")
_REQUEST_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:")
_REQUEST_ID_MAX_LENGTH = 128

if TYPE_CHECKING:
    pass


class Ask(BaseModel):
    """One feedback event submitted by a client.

    Attributes:
        user: User id.
        item: Item id.
        signal: One of 'like', 'dislike', 'view', 'purchase'.
    """

    user: int = Field(..., ge=0, description="User id.")
    item: int = Field(..., ge=0, description="Item id.")
    signal: Literal["like", "dislike", "view", "purchase"] = Field(
        ..., description="Feedback signal type."
    )


class Tell(BaseModel):
    """Response from /v1/feedback.

    Attributes:
        queued: Whether the event was queued.
        buffer_size: Current buffer size after queuing.
    """

    queued: bool
    buffer_size: int


class Rollback(BaseModel):
    """Response from /v1/rollback.

    Attributes:
        restored_version: Version after rollback.
    """

    restored_version: int


class Stats(BaseModel):
    """Response from /v1/stats.

    Attributes:
        events_buffered: Number of events in the buffer.
        updates_applied: Number of updates applied.
        last_loss: Last training loss.
        valid_loss: Last validation loss.
        current_version: Current model version.
        cooldown_until: Timestamp until which updates are paused.
    """

    events_buffered: int
    updates_applied: int
    last_loss: float | None
    valid_loss: float | None
    current_version: int
    cooldown_until: float


def create(
    loader: Loader | None = None,
    *,
    secret_provider: auth.SecretProvider | None = None,
    rate_limit_per_minute: int = 60,
    admin_limit_per_minute: int = 10,
    trusted_proxy_cidrs: tuple[str, ...] | None = None,
    metrics_enabled: bool = True,
    metrics_path: str = "/metrics",
) -> FastAPI:
    """Create a FastAPI app.

    The loader must have a ``"default"`` factory registered. Any request
    handler that needs the live pipeline calls ``loader.get("default")``
    and surfaces ``503`` if the factory is missing or fails. Hard-coding a
    random-weight stub pipeline is **not** supported — a deployment that
    serves without a registered factory must fail closed, not silently
    return nonsense from an untrained model.

    Args:
        loader: A pre-configured :class:`morel.serve.Loader`. If ``None``,
            an empty loader is created and every request returns ``503``.
        secret_provider: Optional external secret resolver. The default reads
            environment variables and mounted ``*_FILE`` references.
        rate_limit_per_minute: Read-endpoint budget per IP per minute.
        admin_limit_per_minute: Admin-endpoint budget per IP per minute.
        trusted_proxy_cidrs: Networks allowed to supply ``X-Forwarded-For``.
        metrics_enabled: Whether to expose the Prometheus endpoint.
        metrics_path: Path at which Prometheus metrics are exposed.

    Returns:
        Configured :class:`FastAPI` instance.
    """
    auth.assert_(secret_provider)  # noqa: PT009 - public auth configuration check
    auth.assert_production(secret_provider)
    app = FastAPI(title="morel inference", version=__version__)
    app.state.metrics_registry = Registry()
    app.state.loader = loader or Loader()
    app.state.updater_enabled = True
    app.state.pipeline_factory = None
    app.add_middleware(
        ObserveMiddleware,
        metrics_enabled=metrics_enabled,
        metrics_path=metrics_path,
        request_id_factory=_request_id,
    )
    proxy_cidrs = (
        trusted_proxy_cidrs
        if trusted_proxy_cidrs is not None
        else tuple(
            value.strip()
            for value in os.environ.get("MOREL_TRUSTED_PROXY_CIDRS", "").split(",")
            if value.strip()
        )
    )
    request_limiter = Limiter()
    request_limiter.configure(
        per_minute_read=rate_limit_per_minute,
        per_minute_admin=admin_limit_per_minute,
        trusted_proxy_cidrs=proxy_cidrs,
    )
    read_limit = ratelimit_dependency("read", request_limiter)
    admin_limit = ratelimit_dependency("admin", request_limiter)
    require_read = auth.dependency("read", secret_provider)
    require_admin = auth.dependency("admin", secret_provider)

    @app.exception_handler(HTTPException)  # type: ignore[untyped-decorator]
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        """Return one stable error envelope for expected HTTP failures."""
        request_id = getattr(request.state, "request_id", "unknown")
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"http_{exc.status_code}",
                    "message": detail,
                    "request_id": request_id,
                }
            },
            headers={**(exc.headers or {}), "X-Request-ID": request_id},
        )

    @app.exception_handler(RequestValidationError)  # type: ignore[untyped-decorator]
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Return validation failures without leaking an unstable traceback."""
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "request_validation_failed",
                    "message": "request payload failed validation",
                    "request_id": request_id,
                    "fields": [
                        {
                            "loc": list(error.get("loc", ())),
                            "msg": str(error.get("msg", "invalid value")),
                            "type": str(error.get("type", "value_error")),
                        }
                        for error in exc.errors()
                    ],
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(Exception)  # type: ignore[untyped-decorator]
    async def internal_error(request: Request, exc: Exception) -> JSONResponse:
        """Sanitize unexpected failures while retaining an operator trace."""
        request_id = getattr(request.state, "request_id", "unknown")
        log.exception(
            "unexpected serving failure",
            extra={"request_id": request_id, "path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "unexpected serving failure; see server logs with the request id",
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @app.get("/health", response_model=Health)  # type: ignore[untyped-decorator]
    def health() -> Health:
        """Liveness probe: process is alive.

        Returns:
            Health: Service status and version.
        """
        return Health(status="ok", version=__version__)

    @app.get("/health/ready")  # type: ignore[untyped-decorator]
    def readiness() -> dict[str, Any]:
        """Readiness probe: a real pipeline can be loaded.

        Returns:
            200 with a ready report if the registered factory produces
            a pipeline; 503 with the failure reason otherwise.
        """
        try:
            pipeline = app.state.loader.get("default")
        except Error as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if not is_serving_pipeline(pipeline):
            raise HTTPException(
                status_code=503,
                detail="loaded factory returned an incompatible pipeline",
            )
        return {
            "status": "ready",
            "loader_keys": app.state.loader.registered(),
            "items": pipeline.item_count if pipeline is not None else 0,
        }

    @app.get(metrics_path)  # type: ignore[untyped-decorator]
    def metrics() -> Any:  # body served by the middleware above
        if not metrics_enabled:
            raise HTTPException(status_code=404, detail="metrics endpoint disabled")
        return metrics_response(app.state.metrics_registry)

    @app.post("/v1/complete", response_model=Done)  # type: ignore[untyped-decorator]
    def complete(
        payload: Fill,
        _: None = Depends(require_read),
        __: None = Depends(read_limit),
    ) -> Done:
        """Completion endpoint.

        Returns 503 if no real ``"default"`` factory is registered with
        the loader. The dimensions of the returned tensors are whatever
        the loaded pipeline reports — never the hardcoded 4/2 stubs the
        previous build silently served.
        """
        if len(payload.items) > MAX_ITEMS_PER_REQUEST:
            raise HTTPException(
                status_code=413,
                detail=f"items exceeds {MAX_ITEMS_PER_REQUEST}-item cap",
            )
        try:
            pipeline = app.state.loader.get("default")
        except Error as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if not is_serving_pipeline(pipeline):
            raise HTTPException(
                status_code=503,
                detail="loaded factory returned an incompatible pipeline",
            )
        completed = run(pipeline, payload)
        return Done(completed=serialize(completed))

    @app.post("/v1/recommend", response_model=List)  # type: ignore[untyped-decorator]
    def recommend(
        payload: Query,
        request: Request,
        _: None = Depends(require_read),
        __: None = Depends(read_limit),
    ) -> List:
        """Recommendation endpoint.

        Scores the user against the loaded recommender and returns the
        top-``top`` items by predicted score. Falls back to 503 when
        no ``"default"`` factory has been registered, instead of
        returning a uniformly-fake ranking.
        """
        try:
            pipeline = app.state.loader.get("default")
        except Error as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        items = suggest(
            pipeline,
            payload,
            request_id=getattr(request.state, "request_id", "unknown"),
        )
        return List(items=items)

    @app.post("/v1/feedback", response_model=Tell)  # type: ignore[untyped-decorator]
    def feedback(
        payload: Ask,
        _: None = Depends(require_admin),
        __: None = Depends(admin_limit),
    ) -> Tell:
        """Feedback endpoint."""
        if not getattr(app.state, "updater_enabled", True):
            raise HTTPException(status_code=503, detail="Updater disabled")
        updater = getattr(app.state, "updater", None)
        if updater is None:
            raise HTTPException(status_code=503, detail="Updater not mounted")
        updater.accept(user=payload.user, item=payload.item, signal=payload.signal)
        return Tell(queued=True, buffer_size=int(updater.stats()["events_buffered"]))

    @app.post("/v1/rollback", response_model=Rollback)  # type: ignore[untyped-decorator]
    def rollback(
        steps: int = FastAPIQuery(
            default=1,
            ge=1,
            le=MAX_ROLLBACK_STEPS,
            description=f"Number of versions to restore, capped at {MAX_ROLLBACK_STEPS}.",
        ),
        _: None = Depends(require_admin),
        __: None = Depends(admin_limit),
    ) -> Rollback:
        """Rollback endpoint."""
        updater = getattr(app.state, "updater", None)
        if updater is None:
            raise HTTPException(status_code=503, detail="Updater not mounted")
        return Rollback(restored_version=int(updater.rollback(steps=steps)))

    @app.get("/v1/stats", response_model=Stats)  # type: ignore[untyped-decorator]
    def stats(
        _: None = Depends(require_admin),
        __: None = Depends(admin_limit),
    ) -> Stats:
        """Stats endpoint."""
        updater = getattr(app.state, "updater", None)
        if updater is None:
            raise HTTPException(status_code=503, detail="Updater not mounted")
        s = updater.stats()
        last_loss = float(s["last_loss"])
        valid_loss = float(s["valid_loss"])
        return Stats(
            events_buffered=int(s["events_buffered"]),
            updates_applied=int(s["updates_applied"]),
            last_loss=last_loss if math.isfinite(last_loss) else None,
            valid_loss=valid_loss if math.isfinite(valid_loss) else None,
            current_version=int(s["current_version"]),
            cooldown_until=float(s["cooldown_until"]),
        )

    return app


# Re-export for callers that want the dependency callables by name.
require_read = auth.dependency("read")
require_admin = auth.dependency("admin")


def run(pipeline: ServingPipeline, payload: Fill) -> dict[str, Any]:
    """Run completion for item ids in the loaded corpus.

    The serving contract requires a pipeline with an attached feature corpus,
    modality mask, and item graph. It never fabricates zero-valued features.
    """
    import numpy as np
    import torch

    items = payload.items
    corpus = pipeline.cfeat
    corpus_mask = pipeline.cmask
    adjacency = pipeline.cadj
    if not isinstance(corpus, dict) or corpus_mask is None or adjacency is None:
        raise HTTPException(
            status_code=503,
            detail="loaded pipeline has no attached feature corpus",
        )
    first = next(iter(corpus.values()), None)
    if first is None:
        raise HTTPException(status_code=503, detail="loaded pipeline feature corpus is empty")
    count = int(first.shape[0])
    indices = np.asarray(items, dtype=np.int64)
    if np.any(indices < 0) or np.any(indices >= count):
        raise HTTPException(status_code=422, detail=f"item ids must be in [0, {count})")
    features = {
        name: torch.from_numpy(np.asarray(values, dtype=np.float32)[indices])
        for name, values in corpus.items()
    }
    mask_t = torch.from_numpy(np.asarray(corpus_mask, dtype=np.float32)[indices])
    output = pipeline(
        features,
        mask_t,
        adjacency=adjacency,
        index=torch.from_numpy(indices),
        training=False,
    )
    if payload.modalities:
        return {
            name: tensor for name, tensor in output.completed.items() if name in payload.modalities
        }
    completed: dict[str, Any] = output.completed
    return completed


def suggest(
    pipeline: ServingPipeline,
    payload: Query,
    *,
    request_id: str = "unknown",
) -> list[Pick]:
    """Return the top-``top`` items for a user via the loaded recommender.

    Fails closed when the pipeline has no recommender. A deployment that
    never wired a ranker must not return plausible-looking fabricated scores.
    """
    import logging

    log = logging.getLogger("morel.serve.recommend")

    if not is_serving_pipeline(pipeline):
        raise HTTPException(
            status_code=503,
            detail="loaded factory returned an incompatible pipeline",
        )
    top = max(1, int(payload.top))
    recommender = pipeline.recommender
    if recommender is None:
        log.error(
            "loaded pipeline has no recommender; refusing to fabricate ranking",
            extra={"user": payload.user, "top": top},
        )
        raise HTTPException(
            status_code=503,
            detail="loaded pipeline has no recommender",
        )
    import torch

    item_count = pipeline.item_count
    user_count = pipeline.user_count
    if payload.user >= user_count:
        raise HTTPException(status_code=422, detail=f"user id must be in [0, {user_count})")
    if item_count <= 0:
        raise HTTPException(status_code=503, detail="loaded recommender has no catalog items")
    item_ids = torch.arange(item_count, dtype=torch.long).unsqueeze(0)
    user_id = torch.tensor([int(payload.user)], dtype=torch.long)
    try:
        with torch.no_grad():
            scores = pipeline.score(user_id, item_ids.squeeze(0)).squeeze(0)
    except HTTPException:
        raise
    except (Error, IndexError, OSError, RuntimeError, TypeError, ValueError) as exc:
        log.exception(
            "recommender scoring failed",
            extra={"request_id": request_id, "user": payload.user, "top": top},
        )
        raise HTTPException(
            status_code=503,
            detail="recommender scoring failed; see server logs with the request id",
        ) from exc
    k = min(top, item_count)
    topk = torch.topk(scores, k=k)
    return [
        Pick(item=int(idx), score=float(score))
        for idx, score in zip(topk.indices.tolist(), topk.values.tolist(), strict=False)
    ]


def count(app: FastAPI) -> int:
    """Return the current request count from the in-app counter."""
    return int(getattr(app.state, "request_count", 0))


def _request_id(value: str) -> str:
    """Return a safe request correlation id or generate one.

    Client-provided ids are retained only when they are short, ASCII, and
    limited to header/log-safe token characters. This prevents control
    characters from reaching response headers or structured log fields.
    """
    candidate = value.strip()
    if (
        0 < len(candidate) <= _REQUEST_ID_MAX_LENGTH
        and candidate.isascii()
        and all(character in _REQUEST_ID_CHARS for character in candidate)
    ):
        return candidate
    return uuid.uuid4().hex


__all__ = [
    "Ask",
    "Rollback",
    "Stats",
    "Tell",
    "create",
    "run",
    "suggest",
]
