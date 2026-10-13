"""Tests for morel.serve."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from morel.core.errors import Model
from morel.serve import Loader, create, is_serving_pipeline
from morel.serve.schema import (
    MAX_ITEMS_PER_REQUEST,
    MAX_MODALITIES_PER_REQUEST,
    MAX_ROLLBACK_STEPS,
)


async def get(client: httpx.AsyncClient, path: str, **kwargs) -> httpx.Response:
    """Issue a GET and return the response."""
    return await client.get(path, **kwargs)


async def post(client: httpx.AsyncClient, path: str, **kwargs) -> httpx.Response:
    """Issue a POST and return the response."""
    return await client.post(path, **kwargs)


def make(app) -> httpx.AsyncClient:
    """Build an async httpx test client.

    Uses ``httpx.ASGITransport`` directly, which dispatches through the
    ASGI app without going through anyio.abc.BlockingPortal (deprecated
    by anyio 4).
    """
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )


class StubPipeline:
    """Tiny object that stands in for a morel.Pipeline in tests.

    Records the dims and a built-in scoring path so ``/v1/complete`` and
    ``/v1/recommend`` can run end-to-end against real (not random) output.
    """

    def __init__(self, users: int = 8, items: int = 8, dims: dict[str, int] | None = None) -> None:
        """Initialize deterministic corpus and graph state for serving tests."""
        import numpy as np
        import scipy.sparse as sp

        self.users = users
        self.items = items
        self.dims = dims or {"visual": 4, "text": 2}
        self.cfeat = {
            name: np.zeros((items, dim), dtype=np.float32) for name, dim in self.dims.items()
        }
        self.cmask = np.ones((items, len(self.dims)), dtype=np.float32)
        self.cadj = sp.csr_matrix((items, items), dtype=np.float32)
        self.ui_graph = sp.csr_matrix(np.eye(users, items, dtype=np.float32))

    @property
    def user_count(self) -> int:
        """Return the configured test user count."""
        return self.users

    @property
    def item_count(self) -> int:
        """Return the configured test item count."""
        return self.items

    def __call__(self, features, mask, adjacency=None, index=None, training=False):
        import torch

        n = int(features["visual"].shape[0])

        class _Out:
            def __init__(self, dims: dict[str, int], n: int) -> None:
                self.completed = {
                    name: torch.zeros((n, d), dtype=torch.float32) for name, d in dims.items()
                }

        return _Out(self.dims, n)

    def score(self, users, items):
        """Score through the test recommender using the explicit contract."""
        return self.recommender(users, items.unsqueeze(0), self.ui_graph)

    @property
    def recommender(self) -> StubRecommender:
        return StubRecommender(self.users, self.items)


class StubRecommender:
    """Return deterministic scores based on ``(user, item)`` so top-k is stable."""

    def __init__(self, users: int, items: int) -> None:
        """Initialize a deterministic test ranker."""
        self.users = users
        self.items = items

    def __call__(self, users, items, ui_graph=None) -> object:
        import torch

        scores = torch.zeros((users.shape[0], items.shape[1]), dtype=torch.float32)
        for i in range(users.shape[0]):
            u = int(users[i].item())
            for j in range(items.shape[1]):
                it = int(items[0, j].item())
                scores[i, j] = float((u * 31 + it) % 17) / 17.0
        return scores


def make_app_with_factory():
    """Build a FastAPI app whose loader has the 'default' factory pre-registered."""
    loader = Loader()
    pipeline = StubPipeline()
    loader.register("default", lambda: pipeline)
    return create(loader), loader, pipeline


class Checker:
    """Aggregated test methods for this module."""

    def missing_key_does_not_leak_build_state(self) -> None:
        """A missing registration must not consume an in-flight build slot."""
        from morel.serve.loader import Loader

        loader = Loader(capacity=1, building_capacity=1)
        with pytest.raises(Model, match="no factory registered"):
            loader.get("missing")
        assert loader.building == {}
        loader.register("real", lambda: object())
        assert loader.get("real") is not None

    def runtime_factory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The importable multi-worker factory supports empty and real bundles."""
        from morel.serve import runtime

        monkeypatch.delenv("MOREL_SERVE_MODEL_DIR", raising=False)
        empty = runtime.create_app()
        assert empty.state.loader.registered() == []

        monkeypatch.setenv("MOREL_SERVE_MODEL_DIR", "/trusted/run")
        monkeypatch.setattr(runtime, "from_run", lambda _: StubPipeline())
        loaded = runtime.create_app()
        assert loaded.state.loader.registered() == ["default"]
        assert loaded.state.loader.get("default").items == 8

    def capacity(self) -> None:
        with pytest.raises(ValueError, match="capacity must be positive"):
            Loader(capacity=0)

    def protocol(self) -> None:
        """The serving boundary accepts structural pipeline implementations only."""
        assert is_serving_pipeline(StubPipeline())
        assert not is_serving_pipeline(object())

    def validated_factory(self) -> None:
        """Registered production factories reject incompatible results before caching."""
        loader = Loader()
        loader.register("default", lambda: object(), validator=is_serving_pipeline)
        with pytest.raises(Model, match="incompatible value"):
            loader.get("default")
        assert loader.keys() == []
        loader.register("default", lambda: StubPipeline(), validator=is_serving_pipeline)
        assert loader.get("default").items == 8

    def caches(self) -> None:
        loader = Loader(capacity=2)
        calls = []

        def factory():
            calls.append(1)
            return object()

        a = loader.get("k1", factory)
        b = loader.get("k1", factory)
        assert a is b
        assert len(calls) == 1

    def evicts(self) -> None:
        loader = Loader(capacity=2)
        loader.get("a", lambda: object())
        loader.get("b", lambda: object())
        loader.get("c", lambda: object())
        assert "a" not in loader.cache

    def key(self) -> None:
        loader = Loader()
        with pytest.raises(ValueError, match="key must be a non-empty string"):
            loader.get("", lambda: object())

    def missing_factory(self) -> None:
        """A request against an unregistered key fails fast with 503, not a stub."""
        from morel.core.errors import Model

        loader = Loader()
        create(loader)
        with pytest.raises(Model, match="no factory registered"):
            loader.get("default")

    def duplicate(self) -> None:
        """Re-registering a key evicts the cached pipeline."""
        loader = Loader()
        a, b = object(), object()
        loader.register("p", lambda: a)
        assert loader.get("p") is a
        loader.register("p", lambda: b)
        assert loader.get("p") is b

    def factory_timeout(self) -> None:
        """A hung factory does not pin waiters forever; they time out."""
        import threading

        loader = Loader(factory_timeout=0.05)

        def hang() -> object:
            import time

            time.sleep(1.0)
            return object()

        loader.register("p", hang)
        results: list[object] = []

        def waiter() -> None:
            try:
                results.append(loader.get("p"))
            except Exception as exc:
                results.append(exc)

        thread = threading.Thread(target=waiter)
        thread.start()
        thread.join(timeout=2.0)
        assert results
        assert isinstance(results[0], Exception)

    def factory_failure_wakes_waiters(self) -> None:
        """A failed factory releases concurrent callers immediately."""
        import threading
        import time

        loader = Loader(factory_timeout=5.0)
        started = threading.Event()
        release = threading.Event()
        results: list[Exception] = []

        def fail() -> object:
            started.set()
            release.wait(timeout=2.0)
            raise RuntimeError("broken factory")

        def call() -> None:
            try:
                loader.get("p", fail)
            except Exception as exc:
                results.append(exc)

        first = threading.Thread(target=call)
        first.start()
        assert started.wait(timeout=1.0)
        waiter = threading.Thread(target=call)
        waiter.start()
        release.set()
        started_at = time.monotonic()
        first.join(timeout=2.0)
        waiter.join(timeout=2.0)
        assert len(results) == 2
        assert time.monotonic() - started_at < 1.0
        assert "p" not in loader.building

    def build_capacity_fails_closed(self) -> None:
        """A full build map never evicts an active factory or duplicates work."""
        import threading

        from morel.core.errors import Model

        loader = Loader(building_capacity=1, factory_timeout=1.0)
        started = threading.Event()
        release = threading.Event()
        calls = []

        def factory() -> object:
            calls.append("a")
            started.set()
            release.wait(timeout=2.0)
            return object()

        thread = threading.Thread(target=lambda: loader.get("a", factory))
        thread.start()
        assert started.wait(timeout=1.0)
        with pytest.raises(Model, match="concurrent build limit"):
            loader.get("b", lambda: object())
        release.set()
        thread.join(timeout=2.0)
        assert calls == ["a"]

    def factory_interrupt(self) -> None:
        """An interrupted factory must not leave a permanently building key."""
        loader = Loader()

        def interrupt() -> object:
            raise KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            loader.get("p", interrupt)
        assert "p" not in loader.building
        assert loader.keys() == []

    async def health(self) -> None:
        """Liveness probe returns 200 with the service status."""
        async with make(create()) as client:
            r = await get(client, "/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.headers["x-request-id"]

    async def request_id_and_error_envelope(self) -> None:
        """Expected HTTP errors carry a stable envelope and correlation id."""
        async with make(create()) as client:
            r = await post(
                client,
                "/v1/recommend",
                json={"user": 0, "top": 3},
                headers={"X-Request-ID": "audit-123"},
            )
        assert r.status_code == 503
        assert r.headers["x-request-id"] == "audit-123"
        body = r.json()["error"]
        assert body["code"] == "http_503"
        assert body["request_id"] == "audit-123"

    async def validation_error_envelope(self) -> None:
        """Validation errors expose safe field metadata, not raw input."""
        async with make(create()) as client:
            r = await post(client, "/v1/recommend", json={"user": 0, "top": 0})
        assert r.status_code == 422
        body = r.json()["error"]
        assert body["code"] == "request_validation_failed"
        assert body["fields"]
        assert all("input" not in field for field in body["fields"])

    async def unexpected_error_envelope(self) -> None:
        """Unexpected handler failures are sanitized and correlated."""
        app = create()

        async def explode() -> None:
            raise RuntimeError("database password=do-not-leak")

        app.add_api_route("/explode", explode, methods=["GET"])
        async with make(app) as client:
            r = await get(client, "/explode", headers={"X-Request-ID": "internal-123"})
        assert r.status_code == 500
        assert "database password" not in r.text
        assert r.json()["error"] == {
            "code": "internal_error",
            "message": "unexpected serving failure; see server logs with the request id",
            "request_id": "internal-123",
        }

    async def health_ready_with_factory(self) -> None:
        """A registered factory yields a 200 ready response."""
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            r = await get(client, "/health/ready")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ready"
        assert "default" in body["loader_keys"]

    async def health_ready_without_factory(self) -> None:
        """A missing factory yields 503, not a stub 200."""
        app = create()
        async with make(app) as client:
            r = await get(client, "/health/ready")
        assert r.status_code == 503

    async def health_ready_incompatible_factory(self) -> None:
        """Readiness rejects factories that do not satisfy the serving contract."""
        loader = Loader()
        loader.register("default", lambda: object())
        async with make(create(loader)) as client:
            r = await get(client, "/health/ready")
        assert r.status_code == 503
        assert "incompatible pipeline" in r.json()["error"]["message"]

    async def health_version_matches_package(self) -> None:
        """Health and OpenAPI expose the generated package version."""
        from morel import __version__

        async with make(create()) as client:
            health = await get(client, "/health")
            openapi = await get(client, "/openapi.json")
        assert health.json()["version"] == __version__
        assert openapi.json()["info"]["version"] == __version__

    async def metrics(self) -> None:
        """``/metrics`` returns the Prometheus text exposition body."""
        async with make(create()) as client:
            await get(client, "/health")
            r = await get(client, "/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("content-type", "")
        body = r.text
        assert "morel_requests_total" in body
        assert "morel_request_duration_seconds" in body

    async def metrics_isolation(self) -> None:
        """Separate app instances must not share request counters."""
        first = create()
        second = create()
        async with make(first) as first_client, make(second) as second_client:
            await get(first_client, "/health")
            first_metrics = await get(first_client, "/metrics")
            second_metrics = await get(second_client, "/metrics")
        assert 'endpoint="/health"' in first_metrics.text
        assert 'endpoint="/health"' not in second_metrics.text

    async def metrics_configuration(self) -> None:
        """Metrics can be disabled or mounted at an explicit internal path."""
        disabled = create(metrics_enabled=False)
        custom = create(metrics_path="/internal/metrics")
        async with make(disabled) as disabled_client, make(custom) as custom_client:
            hidden = await get(disabled_client, "/metrics")
            exposed = await get(custom_client, "/internal/metrics")
            old_path = await get(custom_client, "/metrics")
        assert hidden.status_code == 404
        assert exposed.status_code == 200
        assert old_path.status_code == 404

    async def complete(self) -> None:
        """``/v1/complete`` returns the dims the registered pipeline reports."""
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            r = await post(client, "/v1/complete", json={"items": [0, 1, 2]})
        assert r.status_code == 200
        body = r.json()
        assert "visual" in body["completed"]
        assert len(body["completed"]["visual"]) == 3

    async def complete_oversize(self) -> None:
        """Oversized item lists are rejected before the handler runs."""
        app, _, _ = make_app_with_factory()
        big = list(range(MAX_ITEMS_PER_REQUEST + 1))
        async with make(app) as client:
            r = await post(client, "/v1/complete", json={"items": big})
        assert r.status_code in {413, 422}

    async def complete_modalities_are_bounded(self) -> None:
        """Modality selectors cannot create unbounded request-shape work."""
        app, _, _ = make_app_with_factory()
        too_many = ["text"] * (MAX_MODALITIES_PER_REQUEST + 1)
        too_long = ["x" * 129]
        async with make(app) as client:
            count_response = await post(
                client, "/v1/complete", json={"items": [0], "modalities": too_many}
            )
            length_response = await post(
                client, "/v1/complete", json={"items": [0], "modalities": too_long}
            )
        assert count_response.status_code == 422
        assert length_response.status_code == 422

    async def complete_no_factory(self) -> None:
        """Without a registered factory, /v1/complete returns 503, not a stub 200."""
        app = create()
        async with make(app) as client:
            r = await post(client, "/v1/complete", json={"items": [0, 1, 2]})
        assert r.status_code == 503

    async def rollback_steps_are_bounded(self) -> None:
        """Rollback rejects non-positive and excessive loop counts."""
        app = create()
        async with make(app) as client:
            responses = await asyncio.gather(
                *[
                    post(client, f"/v1/rollback?steps={steps}")
                    for steps in (0, -1, MAX_ROLLBACK_STEPS + 1)
                ]
            )
        assert all(response.status_code == 422 for response in responses)

    async def feedback_payload_is_bounded(self) -> None:
        """Feedback rejects invalid IDs and unsupported signal values."""
        app = create()
        async with make(app) as client:
            responses = await asyncio.gather(
                post(client, "/v1/feedback", json={"user": -1, "item": 0, "signal": "like"}),
                post(client, "/v1/feedback", json={"user": 0, "item": -1, "signal": "like"}),
                post(client, "/v1/feedback", json={"user": 0, "item": 0, "signal": "unknown"}),
            )
        assert all(response.status_code == 422 for response in responses)

    async def recommend(self) -> None:
        """``/v1/recommend`` ranks via the recommender, not a uniform fake slice."""
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            r = await post(client, "/v1/recommend", json={"user": 0, "top": 3})
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 3
        scores = [p["score"] for p in items]
        assert scores == sorted(scores, reverse=True)
        assert len(set(scores)) > 1

    async def concurrent_recommendations(self) -> None:
        """Concurrent requests remain isolated and retain correlation IDs."""
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            responses = await asyncio.gather(
                *[post(client, "/v1/recommend", json={"user": i % 8, "top": 3}) for i in range(32)]
            )
        assert all(response.status_code == 200 for response in responses)
        request_ids = [response.headers.get("x-request-id") for response in responses]
        assert all(request_ids)
        assert len(set(request_ids)) == len(request_ids)

    async def mixed_http_load(self) -> None:
        """Concurrent valid, invalid, and oversized requests remain isolated."""
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            requests = [
                post(client, "/v1/recommend", json={"user": i % 8, "top": 3}) for i in range(32)
            ]
            # Include malformed and bounded-input failures in the same event
            # loop turn as valid traffic to exercise shared middleware and
            # error paths.
            requests.extend(
                [
                    post(client, "/v1/recommend", json={"user": 0, "top": 0}),
                    post(
                        client,
                        "/v1/complete",
                        json={"items": list(range(MAX_ITEMS_PER_REQUEST + 1))},
                    ),
                    post(
                        client,
                        "/v1/complete",
                        json={"items": [0], "modalities": ["unknown"]},
                    ),
                ]
            )
            responses = await asyncio.gather(*requests)
        assert all(response.status_code in {200, 422, 503} for response in responses)
        assert all(response.status_code != 500 for response in responses)
        request_ids = [response.headers.get("x-request-id") for response in responses]
        assert all(request_ids)
        assert len(set(request_ids)) == len(request_ids)

    async def sustained_mixed_http_load(self) -> None:
        """Repeated mixed traffic does not produce 500s or lose correlation IDs."""
        _, loader, _ = make_app_with_factory()
        app = create(loader, rate_limit_per_minute=1_000)
        async with make(app) as client:
            for _ in range(5):
                requests = [
                    post(client, "/v1/recommend", json={"user": i % 8, "top": 3}) for i in range(32)
                ]
                requests.extend(
                    [
                        post(client, "/v1/recommend", json={"user": 0, "top": 0}),
                        post(client, "/v1/complete", json={"items": [0], "modalities": ["x"] * 65}),
                    ]
                )
                responses = await asyncio.gather(*requests)
                assert all(response.status_code in {200, 422, 503} for response in responses)
                assert all(response.status_code != 500 for response in responses)
                assert all(response.headers.get("x-request-id") for response in responses)

    async def rate_limit_isolation(self) -> None:
        """Separate app instances must not share client token buckets."""
        first = create(rate_limit_per_minute=1)
        second = create(rate_limit_per_minute=1)
        async with make(first) as first_client, make(second) as second_client:
            first_response = await post(first_client, "/v1/recommend", json={"user": 0, "top": 1})
            second_response = await post(second_client, "/v1/recommend", json={"user": 0, "top": 1})
        assert first_response.status_code == 503
        assert second_response.status_code == 503

    async def recommend_hides_internal_error(self) -> None:
        """Recommender failures expose a safe message, not exception details."""

        class ExplodingRecommender(StubRecommender):
            def __call__(self, users, items, ui_graph=None) -> object:
                raise RuntimeError("database password=do-not-leak")

        class ExplodingPipeline(StubPipeline):
            @property
            def recommender(self) -> ExplodingRecommender:
                return ExplodingRecommender(self.users, self.items)

        loader = Loader()
        loader.register("default", ExplodingPipeline)
        async with make(create(loader)) as client:
            r = await post(client, "/v1/recommend", json={"user": 0, "top": 3})
        assert r.status_code == 503
        assert "database password" not in r.text
        assert "request id" in r.json()["error"]["message"]

    async def recommend_no_factory(self) -> None:
        """Without a registered factory, /v1/recommend returns 503, not a stub."""
        app = create()
        async with make(app) as client:
            r = await post(client, "/v1/recommend", json={"user": 0, "top": 3})
        assert r.status_code == 503

    async def recommend_invalid_user(self) -> None:
        """User ids outside the loaded model are rejected before scoring."""
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            r = await post(client, "/v1/recommend", json={"user": 8, "top": 3})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "http_422"

    async def recommend_without_ranker(self) -> None:
        """A loaded pipeline without a ranker fails closed instead of fabricating scores."""
        loader = Loader()
        loader.register("default", lambda: object())
        app = create(loader)
        async with make(app) as client:
            r = await post(client, "/v1/recommend", json={"user": 0, "top": 3})
        assert r.status_code == 503

    async def auth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bearer-token auth gates /v1/complete and accepts the right token."""
        monkeypatch.setenv("MOREL_AUTH_TOKEN", "s3cr3t")
        app, _, _ = make_app_with_factory()
        async with make(app) as client:
            r = await post(client, "/v1/complete", json={"items": [0]})
            assert r.status_code == 401

            r = await post(
                client,
                "/v1/complete",
                json={"items": [0]},
                headers={"authorization": "Bearer wrong"},
            )
            assert r.status_code == 401

            r = await post(
                client,
                "/v1/complete",
                json={"items": [0]},
                headers={"authorization": "Bearer s3cr3t"},
            )
            assert r.status_code == 200
