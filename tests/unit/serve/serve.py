"""Tests for morel.serve."""

from __future__ import annotations

import httpx
import pytest

from morel.serve import Loader, create
from morel.serve.schema import MAX_ITEMS_PER_REQUEST


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
        self.users = users
        self.items = items
        self.dims = dims or {"visual": 4, "text": 2}

    def __call__(self, features, mask, adjacency=None, training=False):
        import torch

        n = int(features["visual"].shape[0])

        class _Out:
            def __init__(self, dims: dict[str, int], n: int) -> None:
                self.completed = {
                    name: torch.zeros((n, d), dtype=torch.float32)
                    for name, d in dims.items()
                }

        return _Out(self.dims, n)

    @property
    def recommender(self) -> StubRecommender:
        return StubRecommender(self.users, self.items)


class StubRecommender:
    """Return deterministic scores based on ``(user, item)`` so top-k is stable."""

    def __init__(self, users: int, items: int) -> None:
        self.users = users
        self.items = items

    def __call__(self, users, items) -> object:
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

    def capacity(self) -> None:
        with pytest.raises(ValueError, match="capacity must be positive"):
            Loader(capacity=0)

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

    async def health(self) -> None:
        """Liveness probe returns 200 with the service status."""
        async with make(create()) as client:
            r = await get(client, "/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

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

    async def metrics(self) -> None:
        """``/metrics`` returns the Prometheus text exposition body."""
        async with make(create()) as client:
            r = await get(client, "/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("content-type", "")
        body = r.text
        assert "morel_requests_total" in body

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

    async def complete_no_factory(self) -> None:
        """Without a registered factory, /v1/complete returns 503, not a stub 200."""
        app = create()
        async with make(app) as client:
            r = await post(client, "/v1/complete", json={"items": [0, 1, 2]})
        assert r.status_code == 503

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

    async def recommend_no_factory(self) -> None:
        """Without a registered factory, /v1/recommend returns 503, not a stub."""
        app = create()
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
