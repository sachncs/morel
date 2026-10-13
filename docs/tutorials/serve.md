# Tutorial 3 — serve over HTTP

This tutorial shows how to wrap a trained pipeline in the morel
HTTP server, with auth, rate limiting, and the readiness probe the
production stack expects.

## What the server does

The `morel serve` command starts a FastAPI application on
`--host` / `--port`. It exposes:

- `GET /health` — liveness probe (always 200 while the process is up).
- `GET /health/ready` — readiness probe that confirms a "default"
  pipeline factory is registered.
- `GET /metrics` — Prometheus exposition.
- `POST /v1/complete` — complete missing modalities for a list of item ids.
- `POST /v1/recommend` — rank items for one user.
- `POST /v1/feedback` — queue a feedback event for online update (admin).
- `POST /v1/rollback` — roll back the online updater (admin).
- `GET /v1/stats` — read the updater's current state (admin).

## Step 1 — prepare a serving bundle

The server must load a completed run and its immutable corpus artifacts.
Completion runs created by `morel train completion` contain the required
`features.npz`, `mask.npy`, `item_graph.npz`, and `bipartite.npz` files,
alongside the run's `best.pt` checkpoint.
The loader verifies their config manifests before accepting requests.

Start the server with:

```python
python -m morel serve \
    --model-dir runs/completion \
    --host 0.0.0.0 \
    --port 8080
```

Without `--model-dir`, the process starts only as a liveness shell: model
routes return `503` and readiness remains false. This fail-closed mode is
useful for smoke-testing deployment wiring, but is not a production service.

## Step 2 — sanity-check the routes

```bash
# Liveness: always 200 while the process is alive.
curl -s http://localhost:8080/health | jq .

# Readiness: 200 only when the "default" factory is registered and
# it can build a pipeline.
curl -s http://localhost:8080/health/ready | jq .

# Completion: ask the server to reconstruct a few modalities.
curl -s -X POST http://localhost:8080/v1/complete \
    -H 'content-type: application/json' \
    -d '{"items": [0, 1, 2]}' | jq .

# Recommendation: rank for user 7.
curl -s -X POST http://localhost:8080/v1/recommend \
    -H 'content-type: application/json' \
    -d '{"user": 7, "top": 5}' | jq .

# Prometheus metrics.
curl -s http://localhost:8080/metrics | head -5
```

The completion endpoint caps incoming item lists at 10,000 ids; the
recommendation endpoint returns up to `top` items (default 20).

## Step 3 — enable bearer-token auth (recommended)

Set the relevant tokens in the environment before starting the
server:

```bash
export MOREL_AUTH_TOKEN_READ=read-token-please-change
export MOREL_AUTH_TOKEN_ADMIN=admin-token-please-change
python scripts/serve_app.py
```

Any request to `/v1/*` must include `Authorization: Bearer <token>`.
Admin endpoints (`feedback`, `rollback`, `stats`) require the admin
token specifically — the read token is rejected.

The legacy `MOREL_AUTH_TOKEN` is honored as a read-scope fallback
for upgrade safety; it does **not** grant admin scope.

## Step 4 — turn on rate limiting

The middleware defaults to 60 read requests per minute per IP and 10
admin requests per minute per IP. To change them, pass
`rate_limit_per_minute` / `admin_limit_per_minute` when constructing
the app:

```python
from morel.serve import create

app = create(loader, rate_limit_per_minute=120, admin_limit_per_minute=20)
```

A caller that exceeds the budget sees `429` with a `Retry-After`
header giving the seconds to wait before retrying.

## Step 5 — scrape Prometheus

The `/metrics` endpoint returns counters, histograms, and gauges in
Prometheus text exposition format. The minimum scrape config:

```yaml
scrape_configs:
  - job_name: morel
    metrics_path: /metrics
    static_configs:
      - targets: [morel-host:8080]
```

## Next steps

- [Operations: deploy](../operations/deploy.md) — Docker, Kubernetes, and
  reverse-proxy options for production.
- [Reference: schema](../reference/api.md) — request and response
  shapes for every endpoint.
