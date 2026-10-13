# Production-readiness status

This page is a current verification index, not a historical phase report.
The complete issue register and staged remediation plan live in
[AUDIT.md](https://github.com/sachncs/morel/blob/master/AUDIT.md).

## Verified locally

The following commands pass in the repository's supported local environment:

```text
pytest -q                         566 passed, 84.08% coverage
ruff check .                      pass
ruff format --check .             pass
mypy morel/                       pass
make lock-check                  pass
pip-audit --strict ...            no known vulnerabilities
make audit-artifact              built wheel installs and imports successfully
make fault-injection              11 targeted failure-path tests pass
make serve-workers-smoke          two-worker lifecycle and fail-closed readiness pass
make serve-model-smoke            two-worker real-checkpoint inference pass
make serve-soak                   bounded concurrent two-worker HTTP soak pass
docker build + health smoke      image builds; liveness 200; readiness 503 without model
pnpm test:e2e --project=chromium  14 passed
```

The browser suite covers mobile navigation, focus trapping, Escape handling,
theme persistence, clipboard feedback, reduced motion, WCAG A/AA axe checks,
canonical links, and rendered-link resolution. The same suite also passes
against a Pages-shaped `/morel/` artifact.

## Current safety boundaries

- Production serving requires `MOREL_ENV=production` plus separate read and
  admin credentials.
- Production startup requires a serving bundle path through `--model-dir` or
  `MOREL_SERVE_MODEL_DIR`; development may start fail-closed without one.
- Metrics exposure and the Prometheus route are explicit validated serving
  settings rather than an undocumented hard-coded deployment assumption.
- Serving rate limits, model-factory timeout, and trusted proxy CIDRs are
  validated in `Config.serve` and are no longer hard-coded only in the app.
- Serving also validates and passes bounded per-worker concurrency,
  keep-alive, graceful-shutdown, and request-recycling settings to Uvicorn.
- Serving bounds retrieved graph nodes and fails closed with a typed domain
  error when the configured retrieval budget is exceeded.
- Serving bundle loading warms graph positional encodings before readiness,
  preventing the first live request from paying the graph eigensolver cost.
- Serving loads checkpoints with `weights_only=True` and validates their
  schema and configuration hash.
- The legacy arbitrary-pickle loader is isolated in
  `morel.train.legacy.load_trusted`, gated behind an explicit
  `acknowledge_risk=True` argument, and never used by serving. The old
  `checkpoint.unsafe` name is retained only as a compatibility shim.
- Reverse-proxy client addresses are trusted only when their CIDRs are listed
  in `MOREL_TRUSTED_PROXY_CIDRS`.
- Model serving fails closed when a real pipeline, corpus, graph, or
  recommender is unavailable.

## Not yet verified or published

- The redesigned site has not been pushed to `master`; the public GitHub Pages
  URL still serves the previous build.
- The rebuilt Pages artifact includes a compatibility redirect at `/docs/` for
  older inbound links; the live route remains unverified until deployment.
- The production Docker image now builds locally and in CI with CPU-only
  PyTorch, explicit serving dependencies, a non-root writable log directory,
  and a health/readiness smoke contract.
- CI now installs the exact built wheel, scans the production image for
  high/critical OS and library vulnerabilities, and runs a local-environment
  vulnerability audit in addition to the hash-pinned lockfile audit. An
  artifact SBOM is generated from the runtime lock during release.
- A bounded repeated mixed-traffic test, named `make fault-injection` gate,
  two-worker lifecycle smoke, and bounded concurrent HTTP soak are release
  gates. A 60-second local soak also passes with four concurrent clients;
  production-scale full-load characterization and rollback drills remain open.
- Critical-module coverage is now gated separately for serving, pipeline, CLI,
  and checkpoint loading via `make audit-critical`.
- Malformed HTTP payload property coverage and data-stream boundary tests are
  present; malformed-artifact and broader configuration fuzz coverage remains
  incomplete.
- Streaming co-occurrence construction groups records by user and enforces a
  directed-edge accumulation budget, failing with a domain error before a
  high-degree input can trigger an unbounded quadratic allocation.
- The retrieval encoder uses batched gathers for padded subgraphs; MAGE shares
  one relevance and anchor-normalization index across a batch and lazily
  materializes active neighbor rows. ACS uses compiled SciPy shortest-path
  traversal. The bounded local 1k-item benchmark measures approximately 969
  ms; the 10k-item/32-query end-to-end smoke measures approximately 7.9 s
  locally after the ACS change. These are capacity signals, not production
  SLOs: representative hardware thresholds and CPU transformer capacity
  planning remain open. Shift-invert Laplacian positional encoding for a
  10k-node graph measures approximately 30 ms locally, and persisted/warmed
  graph encodings keep that cost out of the first request.
- Repeated recommendation scores reuse an explicit completed-catalog cache;
  the cache is invalidated on corpus attachment and when training mode begins.
- External deployment observability, rollback, and alert drills remain open.
