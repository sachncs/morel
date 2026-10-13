# morel — Deployment

## Docker

A multi-stage `Dockerfile` produces a slim runtime image:

```bash
docker build -t morel:latest .
docker run -p 8080:8080 -v "$PWD/runs/completion:/model:ro" morel:latest \
  morel serve --model-dir /model --host 0.0.0.0 --port 8080
```

The runtime image runs as a non-root user and includes a `HEALTHCHECK`.

The local two-worker lifecycle can be checked without a model bundle:

```bash
make serve-workers-smoke
```

This starts an importable Uvicorn factory with two workers, verifies repeated
liveness responses, confirms readiness fails closed with HTTP 503, and checks
clean shutdown.

## docker-compose

```bash
docker compose up morel-serve
```

Mounts the local `data/` and `checkpoints/` read-only.

## Environment variables

- `MOREL_DATA_DIR` — root data directory (default `./data`).
- `MOREL_AUTH_TOKEN_READ` — bearer-token for read-only inference endpoints.
- `MOREL_AUTH_TOKEN_ADMIN` — separate bearer-token for feedback, rollback, and
  stats endpoints.
- `MOREL_AUTH_TOKEN_READ_FILE` / `MOREL_AUTH_TOKEN_ADMIN_FILE` — mounted secret
  file alternatives for the corresponding direct token variables. Set only one
  source per scope; production validates both resolved secrets before startup.
- `MOREL_AUTH_TOKEN` — legacy read-scope fallback; do not use it for new
  production deployments.
- `MOREL_AUTH_ENABLED` — set to `1` to require a token even in environments
  that otherwise disable auth.
- `MOREL_ENV=production` — requires separate read and admin bearer tokens at
  startup; each must be at least 16 characters and the two values must differ.
- `MOREL_TRUSTED_PROXY_CIDRS` — comma-separated CIDR networks for reverse
  proxies allowed to supply `X-Forwarded-For`. Leave unset when the service
  is directly exposed; forwarded headers are ignored by default.

The `serve` YAML section also accepts bounded worker controls:
`limit_concurrency`, `limit_max_requests`, `timeout_keep_alive`, and
`timeout_graceful_shutdown`. These protect a worker from unbounded connection
pressure and give rolling shutdowns a deterministic deadline. They are
operational settings and do not change the model-bundle configuration hash.

Serving uses the safe checkpoint loader (`weights_only=True`). The legacy
arbitrary-pickle loader lives in `morel.train.legacy.load_trusted`, requires an
explicit `acknowledge_risk=True` call, and must only be used with files from a
trusted origin. The older `morel.train.checkpoint.unsafe` name is a temporary
compatibility shim.

## Health and metrics

- `GET /health` — JSON `{"status": "ok", "version": "..."}`.
- `GET /metrics` — Prometheus exposition.
- `POST /v1/complete` (`{items, modalities}`) — completed modality
  vectors.
- `POST /v1/recommend` (`{user, top}`) — ranked items.

## Scaling

The current single-process `uvicorn` worker is suitable for moderate
throughput. For high-throughput deployments:

1. Front the service with a load balancer.
2. Place a sidecar model loader that warms the LRU before traffic.
3. Enable Prometheus scraping on `/metrics`.
4. Pin the model bundle with an explicit `--model-dir RUN_DIR` argument. The
   CLI validates that bundle before opening the listening socket.

## Kubernetes (sketch)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: morel
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: serve
        image: morel:latest
        args: ["serve", "--host", "0.0.0.0", "--port", "8080"]
        readinessProbe:
          httpGet: { path: /health, port: 8080 }
        livenessProbe:
          httpGet: { path: /health, port: 8080 }
          initialDelaySeconds: 30
        env:
        - name: MOREL_ENV
          value: production
        - name: MOREL_AUTH_TOKEN_READ
          valueFrom: { secretKeyRef: { name: morel, key: read-token } }
        - name: MOREL_AUTH_TOKEN_ADMIN
          valueFrom: { secretKeyRef: { name: morel, key: admin-token } }
```
