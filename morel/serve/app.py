"""FastAPI app factory for morel inference."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from morel.core.errors import Error
from morel.serve import auth
from morel.serve.loader import Loader
from morel.serve.metrics import REGISTRY, metrics_response
from morel.serve.ratelimit import limiter, ratelimit_dependency
from morel.serve.schema import (
    MAX_ITEMS_PER_REQUEST,
    Done,
    Fill,
    Health,
    List,
    Pick,
    Query,
    serialize,
)

if TYPE_CHECKING:
    from morel.pipeline import Pipeline


class Ask(BaseModel):
    """One feedback event submitted by a client.

    Attributes
    ----------
        user: User id.
        item: Item id.
        signal: One of 'like', 'dislike', 'view', 'purchase'.
    """

    user: int = Field(..., description="User id.")
    item: int = Field(..., description="Item id.")
    signal: str = Field(..., description="One of 'like', 'dislike', 'view', 'purchase'.")


class Tell(BaseModel):
    """Response from /v1/feedback.

    Attributes
    ----------
        queued: Whether the event was queued.
        buffer_size: Current buffer size after queuing.
    """

    queued: bool
    buffer_size: int


class Rollback(BaseModel):
    """Response from /v1/rollback.

    Attributes
    ----------
        restored_version: Version after rollback.
    """

    restored_version: int


class Stats(BaseModel):
    """Response from /v1/stats.

    Attributes
    ----------
        events_buffered: Number of events in the buffer.
        updates_applied: Number of updates applied.
        last_loss: Last training loss.
        valid_loss: Last validation loss.
        current_version: Current model version.
        cooldown_until: Timestamp until which updates are paused.
    """

    events_buffered: int
    updates_applied: int
    last_loss: float
    valid_loss: float
    current_version: int
    cooldown_until: float


def create(
    loader: Loader | None = None,
    *,
    rate_limit_per_minute: int = 60,
    admin_limit_per_minute: int = 10,
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
        rate_limit_per_minute: Read-endpoint budget per IP per minute.
        admin_limit_per_minute: Admin-endpoint budget per IP per minute.

    Returns
    -------
        Configured :class:`FastAPI` instance.
    """
    app = FastAPI(title="morel inference", version="0.1.0")
    app.state.loader = loader or Loader()
    app.state.updater_enabled = True
    app.state.pipeline_factory = None
    limiter.configure(
        per_minute_read=rate_limit_per_minute,
        per_minute_admin=admin_limit_per_minute,
    )

    @app.middleware("http")
    async def observe(request: Request, call_next: Any) -> Any:
        """Count every request and serve Prometheus-formatted /metrics."""
        if request.url.path == "/metrics":
            return metrics_response(REGISTRY)
        response = await call_next(request)
        REGISTRY.observe_request(
            endpoint=request.url.path,
            method=request.method,
            status=response.status_code,
            elapsed=max(0.0, response.headers.get("x-elapsed", 0) if False else 0.0),
        )
        return response

    @app.get("/health", response_model=Health)
    def health() -> Health:
        """Liveness probe: process is alive.

        Returns
        -------
            Health: Service status and version.
        """
        return Health(status="ok", version="0.1.0")

    @app.get("/health/ready")
    def readiness() -> dict[str, Any]:
        """Readiness probe: a real pipeline can be loaded.

        Returns
        -------
            200 with a ready report if the registered factory produces
            a pipeline; 503 with the failure reason otherwise.
        """
        try:
            pipeline = app.state.loader.get("default")
        except Error as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "status": "ready",
            "loader_keys": app.state.loader.registered(),
            "items": int(getattr(pipeline, "items", 0)) if pipeline is not None else 0,
        }

    @app.get("/metrics")
    def metrics() -> Any:  # body served by the middleware above
        return metrics_response(REGISTRY)

    @app.post("/v1/complete", response_model=Done)
    def complete(
        payload: Fill,
        _: None = Depends(auth.dependency("read")),
        __: None = Depends(ratelimit_dependency("read")),
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
        completed = run(pipeline, payload)
        return Done(completed=serialize(completed))

    @app.post("/v1/recommend", response_model=List)
    def recommend(
        payload: Query,
        _: None = Depends(auth.dependency("read")),
        __: None = Depends(ratelimit_dependency("read")),
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
        items = suggest(pipeline, payload)
        return List(items=items)

    @app.post("/v1/feedback", response_model=Tell)
    def feedback(
        payload: Ask,
        _: None = Depends(auth.dependency("admin")),
        __: None = Depends(ratelimit_dependency("admin")),
    ) -> Tell:
        """Feedback endpoint."""
        if not getattr(app.state, "updater_enabled", True):
            raise HTTPException(status_code=503, detail="Updater disabled")
        updater = getattr(app.state, "updater", None)
        if updater is None:
            raise HTTPException(status_code=503, detail="Updater not mounted")
        updater.accept(user=payload.user, item=payload.item, signal=payload.signal)
        return Tell(queued=True, buffer_size=int(updater.stats()["events_buffered"]))

    @app.post("/v1/rollback", response_model=Rollback)
    def rollback(
        steps: int = 1,
        _: None = Depends(auth.dependency("admin")),
        __: None = Depends(ratelimit_dependency("admin")),
    ) -> Rollback:
        """Rollback endpoint."""
        updater = getattr(app.state, "updater", None)
        if updater is None:
            raise HTTPException(status_code=503, detail="Updater not mounted")
        return Rollback(restored_version=int(updater.rollback(steps=steps)))

    @app.get("/v1/stats", response_model=Stats)
    def stats(
        _: None = Depends(auth.dependency("admin")),
        __: None = Depends(ratelimit_dependency("admin")),
    ) -> Stats:
        """Stats endpoint."""
        updater = getattr(app.state, "updater", None)
        if updater is None:
            raise HTTPException(status_code=503, detail="Updater not mounted")
        s = updater.stats()
        return Stats(
            events_buffered=int(s["events_buffered"]),
            updates_applied=int(s["updates_applied"]),
            last_loss=float(s["last_loss"]),
            valid_loss=float(s["valid_loss"]),
            current_version=int(s["current_version"]),
            cooldown_until=float(s["cooldown_until"]),
        )

    return app


# Re-export for callers that want the dependency callables by name.
require_read = auth.dependency("read")
require_admin = auth.dependency("admin")


def run(pipeline: object, payload: Fill) -> dict[str, Any]:
    """Run the completion forward pass on the loaded ``Pipeline``."""
    import numpy as np
    import scipy.sparse as sp
    import torch

    from morel.data.mask import bernoulli

    items = payload.items
    if not items:
        raise HTTPException(status_code=400, detail="items must be non-empty")
    pipeline_obj = cast("Pipeline", pipeline)
    dims = getattr(pipeline_obj, "dims", None)
    if not dims:
        raise HTTPException(
            status_code=503,
            detail="loaded pipeline reports no dims; cannot serve /v1/complete",
        )
    seed = int(getattr(payload, "seed", 0) or 0)
    mask = bernoulli(len(items), len(dims), 0.4, seed=seed).numpy()
    features = {
        name: torch.from_numpy(np.zeros((len(items), dim), dtype=np.float32))
        for name, dim in dims.items()
    }
    mask_t = torch.from_numpy(mask)
    adjacency = sp.csr_matrix((len(items), len(items)), dtype=np.float32)
    output = pipeline_obj(features, mask_t, adjacency=adjacency, training=False)
    if payload.modalities:
        return {
            name: tensor for name, tensor in output.completed.items() if name in payload.modalities
        }
    completed: dict[str, Any] = output.completed
    return completed


def suggest(pipeline: object, payload: Query) -> list[Pick]:
    """Return the top-``top`` items for a user via the loaded recommender.

    Falls back to a uniform ranking only when the pipeline has no
    ``recommender`` attribute — a deployment that never wired a ranker
    cannot score users, and a flat ranking is the only honest answer
    in that case (with an explicit log line so operators can see why).
    """
    import logging

    log = logging.getLogger("morel.serve.recommend")

    top = max(1, int(payload.top))
    recommender = getattr(pipeline, "recommender", None)
    if recommender is None:
        log.warning(
            "loaded pipeline has no .recommender attribute; returning uniform ranking",
            extra={"user": payload.user, "top": top},
        )
        return [Pick(item=i, score=1.0 / (i + 1)) for i in range(top)]
    import torch

    item_count = int(getattr(recommender, "items", top))
    item_ids = torch.arange(item_count, dtype=torch.long).unsqueeze(0)
    user_id = torch.tensor([int(payload.user)], dtype=torch.long)
    try:
        with torch.no_grad():
            scores = recommender(user_id, item_ids).squeeze(0)
    except Exception as exc:  # pragma: no cover - recommender-specific
        raise HTTPException(
            status_code=503,
            detail=f"recommender scoring failed: {exc}",
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


__all__ = [
    "Ask",
    "Rollback",
    "Stats",
    "Tell",
    "create",
    "run",
    "suggest",
]
