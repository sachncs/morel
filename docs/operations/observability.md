# Operations — observability

morel emits its runtime signals through the ``morel.core.log``
structured logger and through the Prometheus exposition on
``/metrics``. This page collects the conventions used by both.

## Logging

`configure(level="INFO", structured=True, directory="runs")` is the
default. With `structured=True`, every line is a JSON object:

```json
{
  "time": "2026-09-09T03:23:17.017852+00:00",
  "level": "INFO",
  "name": "morel.app.experiment",
  "message": "experiment.start",
  "dir": "runs/experiment",
  "cfg_hash": "f7b22ad9269c..."
}
```

Standard fields are always present (`time`, `level`, `name`,
`message`). Extra fields flow through the ``extra={}`` argument:

```python
from morel.core.log import get as logger

log = logger("my.module")
log.info("event.name", extra={"uid": 42, "kind": "feedback"})
```

Plain-text mode (`structured=False`) is used by the CLI when no
``Config`` is on disk, so operator errors are still legible on a
terminal.

## Metrics

The inference server exposes Prometheus metrics at ``GET /metrics``.
The minimum scrape config:

```yaml
scrape_configs:
  - job_name: morel
    metrics_path: /metrics
    static_configs:
      - targets: [morel-host:8080]
```

### Counters

| Name | Labels | Meaning |
|------|--------|---------|
| ``morel_requests_total`` | ``endpoint``, ``method``, ``status`` | HTTP requests by endpoint method and response status. |

### Histograms

| Name | Labels | Meaning |
|------|--------|---------|
| ``morel_request_duration_seconds`` | ``endpoint``, ``method`` | Request latency histogram. |

### Gauges

| Name | Meaning |
|------|---------|
| ``morel_updater_events_buffered`` | Items currently in the feedback ring. |
| ``morel_updater_replay_buffered`` | Items in the replay ring. |
| ``morel_updater_updates_applied`` | Cumulative updates committed. |
| ``morel_updater_cooldown_until`` | Epoch seconds until updates resume. |
| ``morel_updater_state`` | ``1`` while updates are running, ``0`` in cooldown. |

### Custom metrics

In your own server module, attach new metrics to the same registry:

```python
from morel.serve.metrics import REGISTRY

@app.get("/internal")
def my_endpoint() -> ...:
    REGISTRY.counter_inc("morel_app_my_total", {"kind": "internal"})
```

The exporter picks them up automatically. Use a stable metric name
spaced by your component (``morel_app_*`` for application-level
metrics) so dashboards and alerts can find them.

## Health and readiness

Two endpoints, deliberately split:

- ``GET /health`` returns ``200 {"status": "ok", "version": "..."}``
  as long as the process is alive. Wire this to your liveness probe.
- ``GET /health/ready`` returns ``200`` when the loader has a
  registered factory and it can produce a pipeline; ``503`` with a
  failure reason otherwise. Wire this to your readiness probe.

A pod that fails the readiness probe is pulled out of the service
load balancer until it recovers. A pod that fails the liveness probe
is restarted.

## Tracing

morel does not emit OpenTelemetry spans by default. To integrate
with a tracing backend, wrap the FastAPI middleware:

```python
from fastapi import FastAPI
from morel.serve import create

app = create(loader)

@app.middleware("http")
async def trace(request, call_next):
    with tracer.start_as_current_span(f"{request.method} {request.url.path}"):
        return await call_next(request)
```

The existing `morel_core_log` logger emits one structured line per
request, so log-based tracing is also viable.

## See also

- [Tutorial: serve over HTTP](../tutorials/serve.md) — first cut.
- [How-to: serve in production](../howto/serve.md) — auth, rate
  limiting, and Kubernetes integration.
