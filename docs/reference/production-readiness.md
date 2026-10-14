# Production-readiness status

This page is a current verification index, not a historical phase report.
The complete issue register and staged remediation plan live in
[AUDIT.md](https://github.com/sachncs/morel/blob/master/AUDIT.md).

## Verified locally

The following commands pass in the repository's supported local environment:

```text
pytest -q                         640 passed, at least 84.57% coverage
ruff check .                      pass
ruff format --check .             pass
mypy morel/                       pass
make lock-check                  pass
pip-audit --strict ...            no known vulnerabilities
make audit-artifact              built wheel installs and imports successfully
make fault-injection              15 targeted failure-path tests pass
make rollback-drill               updater rollback and divergence tests pass
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
- Serving bundle masks and feature arrays are validated for bounded size, numeric
  finiteness, dimensionality, and consistent corpus rows before pipeline assembly.
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

- The redesigned site is deployed from `master`; the live Pages route and its
  `/morel/` base-path browser gate are verified in CI.
- The rebuilt Pages artifact includes a compatibility redirect at `/docs/` for
  older inbound links; the live route is checked after each Pages deployment.
- The production Docker image now builds locally and in CI with CPU-only
  PyTorch, explicit serving dependencies, a non-root writable log directory,
  and a health/readiness smoke contract.
- CI now installs the exact built wheel, scans the production image for
  high/critical OS and library vulnerabilities, and runs a local-environment
  vulnerability audit in addition to the hash-pinned lockfile audit. An
  artifact SBOM is generated from the runtime lock during release.
- Versioned PyPI publication is tag-only and rejects a wheel whose metadata or
  changelog section does not match the semantic-version tag.
- A bounded repeated mixed-traffic test, named `make fault-injection` gate,
  repeatable local `make rollback-drill`, two-worker lifecycle smoke, and
  bounded concurrent HTTP soak are release gates. A 60-second local soak also
  passes with four concurrent clients; production-scale full-load
  characterization and external rollback/alert drills remain open.
- `make serve-model-smoke` now reports p50/p95/p99 recommendation latency and
  fails on the configured p95 budget (`MOREL_MODEL_SMOKE_P95_SECONDS`, default
  30 seconds); production hardware-specific budgets still need calibration.
- The serving failure-policy matrix is directly tested for timeout, domain,
  dependency, programmer, and cancellation behavior; cancellation remains
  outside the HTTP 500 boundary.
- Critical-module coverage is now gated separately for serving, pipeline, CLI,
  and checkpoint loading via `make audit-critical`.
- Malformed HTTP payload property coverage and data-stream boundary tests are
  present; configuration, manifest, and safe-checkpoint boundaries now have
  malformed-input tests and size caps. Empty, isolated, duplicate-edge, and
  self-loop sparse graph cases are covered; arbitrary checkpoint and serving
  mask bytes are covered; broader artifact fuzz coverage
  remains incomplete.
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
- The in-process Prometheus exporter is now required in production and its
  per-worker scrape behavior is documented. `ResolverSecretProvider` provides
  a bounded, sanitized adapter seam for vendor secret managers; a concrete
  provider integration, rollback exercises, and alert drills remain open.
