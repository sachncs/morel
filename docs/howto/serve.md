# How to serve in production

morel's inference server is a small FastAPI app that exposes
completion, recommendation, feedback, rollback, and stats
endpoints behind bearer-token auth and per-IP rate limits. This
guide covers the production-hardened deployment.

## Configuration at a glance

```python
from morel.serve import Loader, create

loader = Loader()
loader.register("default", lambda: build_my_pipeline())

app = create(
    loader,
    rate_limit_per_minute=120,
    admin_limit_per_minute=20,
)
```

`create(...)` returns the configured `FastAPI` app. Pass it to any
ASGI server (uvicorn, hypercorn, granian).

## Auth

Set the env vars before starting the server:

| Variable                  | Scope     | Endpoint set             |
|---------------------------|-----------|--------------------------|
| ``MOREL_AUTH_TOKEN``      | read      | ``/v1/complete``, ``/v1/recommend`` |
| ``MOREL_AUTH_TOKEN_READ`` | read      | Same as above            |
| ``MOREL_AUTH_TOKEN_ADMIN``| admin     | ``/v1/feedback``, ``/v1/rollback``, ``/v1/stats`` |

A missing token disables auth. With a single ``MOREL_AUTH_TOKEN``
set, only read endpoints accept it; admin endpoints return 401.

!!! danger "Production note"
    The legacy ``MOREL_AUTH_TOKEN`` is honored as a read-scope
    fallback. It does **not** grant admin scope. Set
    ``MOREL_AUTH_TOKEN_ADMIN`` explicitly to enable admin endpoints.

## Rate limiting

The default budgets are 60 read requests / minute and 10 admin
requests / minute, keyed by source IP. A request that exceeds the
budget receives ``429 Too Many Requests`` with a ``Retry-After``
header (seconds).

Override:

```python
app = create(loader, rate_limit_per_minute=120, admin_limit_per_minute=20)
```

The limiter map evicts per-IP records after 10 minutes of inactivity
so memory stays bounded under churn. For multi-process deployments,
front the service with a load balancer and reverse-proxy-side rate
limiting — the in-process limiter is per-worker.

## Body size and item lists

The completion endpoint caps the ``items`` list at 10,000 ids (see
``MAX_ITEMS_PER_REQUEST`` in ``morel.serve.schema``). A request
beyond that raises ``422`` from Pydantic's validator before the
handler runs.

For an application-level body-size cap, front the service with
nginx or envoy:

```nginx
client_max_body_size 1m;
```

## Health and readiness

- ``GET /health`` — liveness. Returns ``200 {"status": "ok", "version": "..."}``.
- ``GET /health/ready`` — readiness. Returns ``200`` if the loader's
  registered factory can build a pipeline; ``503`` otherwise.

Wire the two into Kubernetes:

```yaml
livenessProbe:
  httpGet: { path: /health, port: 8080 }
readinessProbe:
  httpGet: { path: /health/ready, port: 8080 }
```

## Prometheus

The ``/metrics`` endpoint emits counters, histograms, and gauges:

- ``morel_requests_total{endpoint, method, status}``
- ``morel_request_duration_seconds{endpoint, method}`` (histogram)
- ``morel_updater_events_buffered``, ``morel_updater_updates_applied``
- ``morel_updater_state`` (gauge)

Minimal scrape config:

```yaml
scrape_configs:
  - job_name: morel
    metrics_path: /metrics
    static_configs:
      - targets: [morel-host:8080]
```

## Logging

The server configures a structured JSON logger. Each line carries the
configured level, a name (e.g. ``morel.serve.app``), and a JSON
payload with the request id and the routed path.

## Container image

```bash
docker build -t morel:latest .
docker run -p 8080:8080 morel:latest morel serve --host 0.0.0.0 --port 8080
```

The shipped ``Dockerfile`` is multi-stage and runs as a non-root
user. ``docker compose up --build`` brings up the full stack.

## See also

- [Tutorial: serve over HTTP](../tutorials/serve.md) — first-cut
  setup with a toy pipeline.
- [Operations: deploy](../operations/deploy.md) — Kubernetes
  skeleton and reverse-proxy tips.
- [Reference: API](../reference/api.md) — request and response
  shapes.
