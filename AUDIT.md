# Morel repository and product-site audit

Date: 2026-10-14
Scope: repository, local Python package, local React site, and the deployed
`https://sachncs.github.io/morel/` page.

## Verification snapshot

- `./.venv-audit/bin/python -m pytest -q`: **584 passed**, at least 84.57% coverage,
  no warnings.
- A clean dev install initially aborted before collection because
  `pytest-asyncio` was missing from `pyproject.toml`; it is now declared.
- `ruff check .`: passes.
- `ruff format --check .`: passes.
- `mypy morel/`: passes with no configuration warnings.
- Ruff now enforces Google-style docstrings across source and tests; the legacy
  NumPy section underlines have been removed.
- Added a generic `FactoryRegistry[T]` with runtime contract validation and
  constructor adapters for encoders, routers, codebooks, completers, and
  recommenders; public `KIND` maps remain available for configuration
  introspection without being the construction mechanism.
- Retrieval strategy resolution now validates the registered callable against
  the runtime `RetrievalStrategy` protocol before execution, closing another
  untyped plugin boundary.
- Release publication is now tag-only and verifies the built wheel version and
  changelog release section against the pushed semantic-version tag before
  PyPI upload.
- The real model-backed two-worker smoke now repeats recommendation requests,
  reports p50/p95/p99 latency, and fails against an explicit configurable p95
  budget; production hardware-specific calibration remains open.
- Checkpoint loading now preserves filesystem `OSError` failures for retry or
  operator handling instead of misclassifying them as corrupt model payloads;
  checkpoint saves use unique sibling temp files with guaranteed cleanup, and
  regression tests cover both permission failures and failed writes.
- Admin rollback requests now bound `steps` to a positive finite range before
  entering the updater loop, preventing query-parameter amplification.
- Feedback requests now enforce non-negative IDs and a closed set of supported
  signal values before events enter the bounded updater buffers.
- Idle updater stats now serialize unavailable non-finite losses as JSON `null`
  instead of allowing an invalid JSON response to break the admin endpoint.
- The serving protocol now requires explicit `user_count`, `item_count`, and
  `score()` capabilities; incomplete structural implementations are rejected
  before caching instead of falling back to reflective dispatch.
- `make audit-critical`: passes with per-subsystem coverage floors for serving
  (79%), pipeline (77%), CLI (71%), and checkpoint loading (84%).
- The corrected forward benchmark uses a bounded 32-query batch; the local
  1k-item case measures approximately **969 ms** for one default-MAGE run.
  After compiled ACS traversal, the 10k-item/32-query end-to-end smoke
  measures approximately **7.9 s** locally: retrieval is about 2.4 s and the
  CPU transformer encoder about 9.2 s under profiling. This is evidence for
  capacity planning, not a production SLO; representative hardware and
  production-shaped retrieval thresholds are still required.
- `pnpm build` in `site/`: passes after `pnpm install --frozen-lockfile`.
- `make lock-check`: passes for the pinned Linux/Python 3.11 target; lock
  regeneration now uses explicit upgrade semantics.
- `pip-audit --strict --disable-pip --requirement requirements.lock`: passes
  with no known vulnerabilities in the runtime lock.
- `make audit-artifact`: passes; installs the exact built wheel into an isolated
  target directory, imports it, validates its embedded version, and checks the
  console entry point. CI additionally audits the environment after installing
  that wheel.
- `docker build --tag morel:local-smoke .` and the production container smoke
  contract pass locally: `/health` returns 200 and `/health/ready` returns 503
  without a model bundle while running as the non-root image user.
- The serving suite includes a bounded mixed HTTP load test with concurrent
  valid, malformed, oversized, and unknown-modality requests, plus isolation
  coverage proving separate app instances do not share rate-limit buckets.
- The serving suite also repeats mixed traffic across five rounds, and the CI
  container smoke starts two Uvicorn workers and probes liveness repeatedly.
- Multi-worker serving now uses an importable Uvicorn factory instead of an
  in-memory app object, which avoids Uvicorn's worker-supervisor refusal and
  validates each worker's model bundle before readiness.
- Added `make serve-workers-smoke`, a repeatable local two-worker lifecycle
  gate that checks liveness, fail-closed readiness, repeated probes, and clean
  shutdown without requiring a model artifact.
- Added `make serve-soak`, a bounded concurrent process-level HTTP gate that
  mixes liveness, fail-closed readiness, malformed payload, and missing-model
  requests against two real Uvicorn workers and requires clean shutdown.
- The bounded soak also passed for 60 seconds with four concurrent clients:
  1,520 liveness responses, 1,758 fail-closed readiness responses, 1,520
  validation responses, and 1,282 expected rate-limit responses, with no
  timeout or worker failure.
- Added `make serve-model-smoke`, which loads the real `runs/completion`
  bundle in two workers and verifies authenticated `/health`, readiness,
  `/v1/complete`, and non-empty `/v1/recommend` responses.
- Added validated serving resource controls for per-worker concurrency,
  keep-alive, graceful shutdown, and request-count recycling. These are passed
  to Uvicorn and excluded from the model-artifact hash so existing bundles
  remain loadable.
- Serving bundle loading now warms graph positional encodings before the
  pipeline becomes ready, moving the expensive first-request computation into
  controlled startup.
- Production preflight now requires a model-bundle path for both the CLI and
  inherited multi-worker runtime; development remains allowed to start
  fail-closed without one.
- Added a validated retrieval-node budget to serving and a shared MAGE
  relevance index for batch requests; oversized retrievals now fail through a
  typed domain error instead of consuming unbounded graph work.
- Hardened streaming ingestion against malformed JSON shapes, invalid bounds,
  malformed sparse chunks, duplicate-edge k-core inflation, and malformed
  metadata records; added regression coverage for each boundary.
- MAGE now materializes adjacency rows lazily for the active subgraph instead
  of building a neighbor map for every catalog node on every query. ACS now
  uses compiled SciPy shortest-path traversal rather than repeated Python
  bit-mask walks; the 10k/32-query smoke improved from 17.5 s to 7.9 s after
  this change. The remaining scale work is representative hardware/SLO
  calibration and CPU transformer capacity planning.
- Added `make fault-injection`, a named gate for loader timeout/failure,
  request sanitization, updater atomicity, checkpoint rejection, and malformed
  HTTP payload behavior.
- Added a final serving middleware safety net for unexpected endpoint failures:
  it logs the request ID and returns a stable sanitized 500 envelope, while
  still recording the request latency sample; both behaviors have regression
  coverage.
- Fixed `make audit-artifact` to select the newest wheel instead of installing
  every stale wheel left in `dist/`, which previously made a valid build fail
  with a misleading dependency-resolution conflict.
- `pnpm test:e2e --project=chromium`: **14 passed** against the built site
  preview, covering mobile navigation focus trapping, Escape/focus restore,
  anchor navigation, theme persistence, clipboard feedback, reduced motion,
  and canonical link targets, plus an axe WCAG A/AA audit with zero
  violations and a rendered-link crawl with no broken destinations.
- The same **14 tests pass** against a `GITHUB_PAGES=1` artifact served at
  `/morel/`, including asset loading under the real Pages base path.
- The site now puts code, measured verification, and quickstart before the
  decorative architecture/adoption sections; performance claims link directly
  to benchmark and readiness evidence, and the local browser/axe suite still
  passes after the information-architecture change.
- `make site-test` and `make site-pages-test` now expose both browser gates as
  repeatable local audit targets.
- `pnpm test:unit`: **4 passed** frontend unit tests for class merging,
  number formatting, verification metadata, and canonical link configuration.
- `make docs-check` now scans the README, MkDocs pages, and site code sample
  for removed public API names and known stale configuration claims.
- CI now builds the site and runs the browser smoke suite on pull requests and
  pushes; the Pages deployment workflow now gates publishing on the same
  base-path browser suite.
- Smoke-tested successfully: `morel data extract --synthetic`, `morel data
  build --synthetic`, `morel render-fidelity`, and `morel eval rank`.
- Rebuilt and smoke-tested the production container with explicit production
  credentials: `/health` returns 200, `/health/ready` returns 503 without a
  model bundle, and `/metrics` returns 200; the image runs as the non-root
  user.
- GitHub Pages deployment `38451394978` published the redesigned artifact after
  the real Linux runner passed all 14 browser checks; `curl -fsSIL
  https://sachncs.github.io/morel/` returns HTTP 200 and the live HTML contains
  the `/morel/` favicon, truthful product copy, and canonical site metadata.

## Implemented in the current worktree

- Added `pytest-asyncio` to the development dependencies and cleared Ruff
  formatting plus mypy's Laplacian return-type failure.
- Made serving fail closed when a recommender is absent, added bounded query
  validation, and recorded real request latency in Prometheus metrics.
- Repaired documentation and GitHub links, removed false production-ready
  wording from the landing page, and made initial performance counters truthful
  instead of rendering zero before animation.
- Reworked the logo into a morel-cap/mycelium graph mark, updated favicon,
  package/docs/social assets, and shifted the palette from saturated purple to
  warm mushroom gold and charcoal.
- Added basic mobile dialog semantics, focus restoration, and Escape-to-close
  behavior to the site navigation.
- Added a validated, manifest-bound serving factory and `morel serve
  --model-dir RUN_DIR`; completion runs now persist the feature/mask/graph
  bundle required by real inference.
- Production CLI startup now eagerly loads the registered run bundle before
  opening the Uvicorn socket, while the reusable library loader remains lazy.
- Removed `del`-based unused-variable workarounds across runtime and test code;
  intentional unused parameters remain explicit in their signatures.
- Bound training checkpoints to the top-level config hash and added an
  end-to-end local smoke test that trains, reloads, and scores a run bundle.
- Added a real `Pipeline.score()` path that uses attached corpus state,
  completion output, the user-item graph, and model-device placement.
- Added [engineering.md](docs/engineering.md) with Google-style Python,
  semi-private naming, typed polymorphism, ownership, security, and review
  rules.
- Added request IDs, stable HTTP error envelopes, validation error handling,
  and production startup checks requiring separate read/admin credentials.
- Production auth now rejects legacy-only credentials, weak tokens, and shared
  read/admin secrets; CI's container fixtures use distinct 16-character test
  tokens.
- Added a serving preflight contract: production startup rejects unstructured
  or DEBUG logging before model loading and socket creation.
- Bounded the completion request's optional modality selector to 64 names and
  128 characters per name, closing an unbounded request-shape/resource
  exposure at the HTTP schema boundary.
- Added request-aware recommender diagnostics and early bounds checks for
  unknown users and empty catalogs.
- Sanitized recommender failure responses so exception details stay in
  request-correlated server logs instead of reaching API clients.
- Added trusted reverse-proxy CIDR handling for rate limiting; forwarded
  client addresses are ignored unless explicitly configured and documented.
- Isolated legacy arbitrary-pickle checkpoint loading in the explicit
  `morel.train.legacy.load_trusted` module, retained the old name only as a
  compatibility shim, and required an explicit risk acknowledgement; the
  production-readiness report documents the trust boundary.
- Added checkpoint schema validation for tensor state, metadata types,
  finite metrics, non-negative epochs, and safe optional sections.
- Hardened LightGCN empty/negative-id handling, simplified the all-masked
  attention fallback, and made MRR linear in catalog width instead of sorting
  every user row.
- Made recommender variation points runtime-checkable through shared
  `Recommender`, `Fits`, and `Normalizes` protocols, and added a contract test
  covering every registered ranker.
- Added a deterministic, hash-pinned lock refresh/check workflow, runtime
  dependency auditing, and a site build job to CI.
- Made the two encoder boundaries explicit as `FeatureEncoder` and
  `GraphEncoder`, retained compatibility aliases for `Feature` and `Enc`, and
  added architecture-contract tests proving both protocols are runtime usable.
- Added Playwright smoke coverage at 360px, 768px, 1024px, and 1440px, and made the E2E command rebuild before
  previewing, eliminating stale local preview state from browser verification.
- Added deterministic desktop and mobile visual baselines for the redesigned
  logo, palette, and first viewport, with reduced-motion capture settings.
- Fixed the mobile navigation sheet so its closed state is explicitly invisible
  rather than merely non-interactive; the visual baseline caught the leaked
  panel pixels.
- Added a real mobile-dialog focus trap and verified it at a 390px viewport.
- Added rendered-link crawling and fixed a real 404 in the footer’s GitHub
  Discussions link by replacing it with the repository’s Pull requests page.
- Added a prefix-aware Pages preview server and gated the Pages deployment on
  the `/morel/` artifact path, preventing root-hosting tests from masking base
  path failures.
- Removed the pytest collection warning caused by importing `ClassVar` into a
  test module.
- Removed unsupported hard-coded recommendation deltas from the product site;
  performance cards now direct users to reproducible local evaluation, and
  stale documentation counts were updated to the current 580/84.60 baseline.
- Corrected deployment documentation to remove unsupported `LOG_LEVEL` and
  `MOREL_MODEL_PATH` controls, and removed a duplicated acquisition docstring
  section.
- Removed `del`-based unused-variable workarounds across runtime and test code;
  intentional unused parameters remain explicit in their signatures.
- Expanded `Config.validate()` into a fail-closed schema boundary for nested
  strings, supported kinds, finite numeric values, ranges, training budgets,
  and evaluation ratios, with negative tests for malformed configuration.
- Nested configuration parsing now rejects unknown keys and non-mapping
  sections instead of silently dropping data or leaking `AttributeError`.
- Narrowed CLI logging fallback handling to expected configuration, YAML, and
  filesystem failures; cancellation and unexpected programming errors are no
  longer silently swallowed there.
- Added a dated `VERIFICATION` source for product-site metrics and synchronized
  the current 580-test/84.60%-coverage evidence across the audit, docs, and site.
- Added the documented `Config.from_dict()` and `Config.from_yaml()` aliases
  with a YAML round-trip regression test, eliminating another public-example
  API mismatch.
- Corrected vectorized relevance aggregation so candidates with no jointly
  observed modality are excluded from the mean instead of diluting it with
  artificial zeros, with a regression test for the sparse-mask case.
- Fixed the updater’s divergence cooldown to honor the validated configured
  `cooldown_seconds` instead of a hard-coded minute, added control-range
  validation, and exposed a repeatable `make rollback-drill` gate for rollback
  and recovery behavior.
- Corrected stale README links to renamed documentation paths and added a
  documentation gate that rejects broken repository-relative README links.
  The security policy now distinguishes the safe production checkpoint path
  from the explicitly acknowledged legacy pickle escape hatch.
- Added Hypothesis property coverage for arbitrary JSON-shaped configuration
  payloads and safely serializable checkpoint payloads, asserting malformed
  inputs fail through domain errors rather than internal exceptions.
- Added a runtime-checkable `ServingPipeline` protocol so incompatible loader
  results fail closed with a stable 503 before serving code dereferences them.
- Fixed loader failure paths so missing registrations do not leak in-flight
  build entries, and concurrent waiters are notified immediately when a
  factory fails instead of waiting for the full watchdog timeout.
- Added a runtime-checkable `RetrievalStrategy` protocol and typed retrieval
  registry, removing object dispatch and the associated operator type escape.
- Added an explicit `FeatureAware` recommender capability and routed completed
  features through it instead of probing optional attributes with `getattr`.
- Made live updater commits atomic with respect to inference by holding the
  model write lock through mutation, validation, rollback, and commit; added a
  concurrency regression proving readers cannot observe partial weights.
- Made loader build-capacity handling fail closed instead of evicting active
  in-flight keys, preventing duplicate factory execution under load.
- Made the serving CLI reject an incompatible loaded factory result before
  opening the Uvicorn socket, with a fail-fast regression test.
- Hardened ranking metrics for empty catalogs and cutoffs wider than the
  catalog, with regression coverage for neutral empty-catalog results.
- Made Prometheus registries app-local so multiple service instances do not
  contaminate one another's request counters; added isolation coverage.
- Introduced the explicit `ModalityMask` value-object name while preserving
  `Mask` as a compatibility alias, removing ambiguity with masking concepts.
- Bound service health and OpenAPI version fields to the generated package
  version and added a regression test; the site now labels the API as v0.1
  rather than claiming an unreleased v1.0.
- Made readiness validate the serving protocol, so an incompatible factory
  result cannot be advertised as ready.

The inventory below is the complete baseline register. Items listed as
implemented above are closed in this worktree but remain regression risks until
the corresponding CI and browser gates are added; the remaining items are
unresolved and stay in the staged plan.

## Current status of the register

The numbered inventory below is intentionally retained as the complete issue
history. This status map prevents historical findings from being mistaken for
open defects:

- **Closed in this worktree:** 1–5, 7–15, 17–20, 23, 26–33, 34–42, 49,
  50–60, and the local/deployed portions of 43–48.
- **Partially addressed:** 6, 16, 19, 21, 22, 24, and 25.
- **Still open:** the partially addressed items listed below; the deployment
  portions of 43–53 are verified by Pages run `38520161516` and the live URL
  check.

The local pipeline boundary now validates modality names and shapes and stores
defensive snapshots of feature, mask, and adjacency inputs; this closes the
mutable-attachment portion of issue 20. The redesigned site is deployed and
rechecked; remaining open work is technical scale, observability integration,
and release operations.

## Issue inventory

### P0 — must fix before calling the project production-ready

54. The Docker build was not production-ready: the Dockerfile began with a
   Python-style triple-quoted string, tried to install the project before
   copying its source, and relied on Git metadata excluded from the build
   context for `setuptools-scm` version discovery; it also copied the wheel
   from the wrong stage path. Container delivery could not reach a reliable
   runtime image, the wheel omitted its optional serving dependencies, and
   unconstrained runtime installation selected a massive CUDA dependency tree
   for CPU deployments; the non-root runtime user also lacked a writable
   default log directory; and a clean runtime process accessed `uvicorn`
   through `sys.modules` without importing it first.

1. `/v1/recommend` can return a fabricated descending uniform ranking when the
   loaded pipeline has no recommender. A serving system must fail closed with a
   503 and an operator-visible error, not return plausible-looking nonsense.
2. `/v1/recommend` calls the recommender without the user-item graph and
   completed item features. The endpoint therefore does not exercise the
   advertised retrieval/completion pipeline and can silently serve an
   ID-embedding-only ranking.
3. `/v1/complete` fabricates zero-valued item features and an empty adjacency
   graph from item IDs. It is not completing real catalog modalities; the API
   contract needs either real feature inputs or an explicit demo-only status.
4. Request latency metrics are always recorded as `0.0` because the ASGI
   middleware contains a permanently false expression instead of timing the
   request. The advertised Prometheus observability is therefore incomplete.
5. The public product page claims “production-ready”, “482 tests · 80%
   coverage”, and benchmark improvements while the deployed UI renders the
   animated stat counters as zero until/while they run and the claims are not
   tied to a generated artifact or release. This is a trust and correctness
   issue, not only a copy issue.
6. **Partially addressed:** The built and deployed site includes a static
   `/docs/` redirect to the canonical documentation tree, so Pages retains a
   working compatibility route. External documentation hosting remains a
   deployment follow-up; the PyPI release workflow now enforces tag/version
   consistency before publication.

### P1 — correctness and security

7. **Closed in this worktree:** The legacy arbitrary-pickle compatibility path
   is isolated in `morel.train.legacy.load_trusted`, requires explicit risk
   acknowledgement, emits a warning, and is documented as outside the safe
   production loader. The old name remains only as a migration shim.

56. **Closed in this worktree:** The `/v1/complete` schema bounded item ids but
    allowed an unbounded list of modality selectors and arbitrarily long names,
    leaving request parsing and downstream feature selection less predictable
    under hostile input.

57. **Closed in this worktree:** The CLI passed an in-memory FastAPI app to
    Uvicorn even when configured with multiple workers. Uvicorn refused that
    configuration and exited after warning, so the advertised worker count was
    not actually served. Multi-worker mode now uses an importable factory and
    validates each worker-local app.

58. **Closed in this worktree:** The artifact gate installed every wheel in
    `dist/`, so stale wheels from earlier builds could conflict with the current
    package and make a valid artifact fail for the wrong reason. The gate now
    selects the newest wheel explicitly.
8. **Closed in this worktree:** `suggest()` catches all recommender exceptions and turns them into a generic
   503, losing structured error classification and making operational diagnosis
   harder. Preserve safe client messages while logging the traceback with a
   request/correlation ID.
9. **Closed in this worktree:** The service has no request correlation ID, structured error envelope, or
   consistent exception-to-status mapping across endpoints.
10. **Closed in this worktree:** Auth is disabled when no token is configured. That is convenient for local
    development but unsafe as a default deployment posture; production startup
    should require explicit auth configuration unless an explicit development
    mode is selected.
11. **Closed in this worktree:** Rate limiting keys directly on `request.client.host`; deployments behind a
    reverse proxy need a documented trusted-proxy policy or the limiter can
    collapse all users into one bucket.
12. **Closed in this worktree:** The checkpoint payload is only shallowly validated. Types/shapes for model,
    optimizer, RNG, epoch, metric, config hash, and extras are not checked
    before use.
13. **Closed in this worktree:** `Light.forward()` calls `.max()` on user/item tensors without handling
    empty inputs, so valid empty-batch or no-result flows can raise unexpectedly.
14. **Closed in this worktree:** `morel/encode/pool.py` contains a dead/incorrect fallback condition in the
    all-masked attention path. The later branch makes the current output finite,
    but the code is misleading and should be reduced to a tested explicit
    all-masked policy.
15. **Closed in this worktree:** `morel/eval/ranking.mrr()` still fully sorts every row despite documenting
    an `argpartition`-style optimization. This is a performance/correctness
    contract mismatch for large catalogs.
16. **Partially addressed:** CLI logging now catches only expected
    configuration/YAML/filesystem failures and preserves cancellation.
    Distributed initialization and API generation now catch only expected
    runtime/import failures. Loader factory failures and expected recommender
    dependency failures now use typed/sanitized serving errors; the global HTTP
    middleware remains a final defensive boundary for unknown programmer or
    dependency failures. The remaining boundaries need continued
    fault-injection coverage and an explicit exception taxonomy.

### P2 — architecture and API design

17. **Closed in this worktree:** The former `Mask`/encoder naming collision is
    resolved with `ModalityMask`, `FeatureEncoder`, and `GraphEncoder`; the
    original `Mask`, `Feature`, and `Enc` names remain documented compatibility
    aliases.
18. **Closed in this worktree:** Recommenders and encoders do not share a single stable runtime contract.
    `Light`, `MF`, and `Pop` are selected through registries but are not unified
    behind a documented abstract interface with capability declarations.
19. **Partially addressed:** Serving factories now accept runtime validators,
    and the CLI/runtime register an explicit serving contract requiring
    `score`, `user_count`, and `item_count` before caching a model. A shared
    `FactoryRegistry[T]` now validates built-in encoder, router, codebook,
    completer, recommender, and retrieval strategy contracts at composition
    time. Optional capabilities elsewhere still use `getattr`; third-party
    extension registration and the remaining protocol boundaries need a typed
    plugin surface.
20. **Closed in this worktree:** `Pipeline.attach()` stores mutable corpus dictionaries/arrays by reference.
    Callers can mutate data after attachment and change inference behavior
    without invalidation or a clear lifecycle boundary.
21. **Closed in this worktree:** `Pipeline.encode()` now performs batched
    indexed gathers per modality and one transformer call over padded
    subgraphs; it no longer loops over batches or nodes. The remaining scale
    cost is retrieval construction, tracked separately below.
22. **Partially addressed:** Relevance and anchor retrieval now build reusable
    normalized indices for each batch, and MAGE avoids rebuilding a full-catalog
    neighbor map per query. A local 10k/32-query anchor comparison measured
    1.73x lower anchor-selection time with the shared index. Serving also
    enforces a validated retrieval-node budget and fails with a typed domain
    error when it is exceeded. A bounded 1k run is
    approximately 969 ms. The 10k Laplacian positional encoding now uses
    shift-invert ARPACK and measures approximately 30 ms locally, down from
    17.1 s with the previous smallest-magnitude solver; large-graph failures
    now raise instead of attempting dense allocation. Compiled ACS traversal
    reduced a 10k/32-query end-to-end smoke from 17.5 s to 7.9 s locally.
    Representative production latency thresholds and CPU transformer capacity
    planning remain open; serving warms persisted or computed encodings at
    startup so the cost is not paid by the first request.
23. **Closed locally; serialized bundles intentionally exclude derived state:**
    `Pipeline.wire()` prepares graph-normalizing rankers once and the serving
    score path reuses that cache without re-hashing the CSR matrix on every
    request. `Light` now owns a content-addressed cache value object, exposes
    explicit invalidation after corpus replacement, and migrates derived
    adjacency state through `Module.to`/`cuda` without serializing it as model
    weights.
24. **Partially addressed:** The loader now supports explicit result validators,
    and production CLI/runtime registrations reject incompatible serving
    pipelines before caching. Unvalidated third-party registrations can still
    defer failure until first access and need a common typed factory surface.
25. **Partially addressed:** Serving budgets, factory timeout, trusted-proxy
   policy, per-worker concurrency, keep-alive, graceful shutdown, request
   recycling, and the production model-bundle requirement are now validated
   and wired into startup. Production startup now requires the app-scoped
   metrics endpoint to remain enabled, and observability documentation covers
   per-worker registry and scrape behavior. Auth accepts bounded mounted-secret
   file references for both scopes and rejects ambiguous direct/file
   configuration. A typed `SecretProvider` seam now supports vendor secret
   managers through `create(secret_provider=...)`; a vendor-specific adapter,
   rollback exercises, and alert drills remain deployment work.

59. **Closed in this worktree:** The streaming co-occurrence builders treated
    every record in a chunk as belonging to one user, creating false
    item-item edges across unrelated users. Their COO accumulators also had no
    hard edge budget, so one high-degree user could force a quadratic Python
    list allocation. Both paths now group items by user and fail closed at a
    validated directed-edge limit.

60. **Closed in this worktree:** The scrollable quickstart and source-code
    blocks were not keyboard-focusable, causing the Pages axe gate to reject
    the redesigned site with `scrollable-region-focusable`. Both blocks now
    expose a keyboard focus target and accessible label; desktop and
    `/morel/` base-path browser gates pass locally.

### P3 — testing and quality gates

26. **Closed in this worktree:** `pytest-asyncio` is absent from dev dependencies, so a fresh environment
    cannot run the configured suite. Add and pin the plugin compatibility.
27. **Closed in this worktree:** The suite passes but has a warning because pytest attempts to collect
    `ClassVar` as a test-like callable. Rename/exclude the offending symbol or
    tighten collection configuration.
28. **Closed in this worktree:** Frontend unit tests now cover pure site
    utilities and published-content contracts; browser interaction,
    accessibility, responsive, and desktop/mobile visual baseline suites cover
    the highest-risk user-facing flows.
29. **Closed in this worktree:** No browser smoke test verifies menu open/close, keyboard focus, theme
    persistence, anchor navigation, copy-to-clipboard, external-link targets,
    or responsive layouts.
30. **Closed in this worktree:** Coverage is aggregated across the whole suite and does not enforce minimum
    coverage for critical serving, CLI, checkpoint, and pipeline modules.
31. **Closed in this worktree:** CI does not run the site build, site link checks, or a production preview
    smoke test in the same change gate as the Python package.
32. **Closed in this worktree:** CI installs and audits the built wheel, scans
    the exact production image for high/critical OS and library vulnerabilities,
    and keeps the hash-pinned lockfile audit as a separate gate. The release
    workflow also retains a lockfile-derived CycloneDX SBOM with the published
    artifacts. Local image scanning remains an optional convenience, not a
    release gate.
33. **Closed in this worktree:** Property and boundary coverage now exercises
    malformed HTTP payloads, checkpoint files, configuration YAML, sparse
    matrix indices, streaming JSON/chunks, duplicate-edge k-core behavior, and
    bounded graph shapes, non-finite weights, and malformed sparse artifacts.
    Persisted sparse graphs now enforce explicit node and edge budgets at save
    and load boundaries, including caller-selectable lower limits for services.

### P4 — style, maintainability, and documentation

34. **Closed in this worktree:** Ruff lint is green, but formatting is not: 12 tracked files fail
    `ruff format --check`.
35. **Closed in this worktree:** The repository lacks a written engineering standard covering Google-style
    Python conventions, public/private/semi-private naming, import boundaries,
    error taxonomy, logging, API stability, and deprecation policy.
36. **Closed in this worktree:** The requested semi-private naming convention is not codified. Internal
    helpers, registries, caches, and extension points use inconsistent exposure
    patterns.
37. **Closed in this worktree:** The OOP/polymorphism boundary is implicit. Some components use ABCs or
    protocols, while others depend on duck typing, string dispatch, or
    coincidental call signatures. Document which variation points are intended
    and enforce them with contracts.
38. **Closed in this worktree:** `mypy` has one concrete failure in `graph/laplacian.py`; the strict typing
    gate is therefore not green despite the configuration claiming strict mode.
39. **Closed in this worktree:** Duplicate issue-template formats (`.yml` and `.md`) create inconsistent
    contribution UX and should be consolidated.
40. **Closed in this worktree:** Several docs and generated-looking reports were
    not automatically checked for freshness. The metrics gate now checks the
    published verification snapshot, and ``make docs-check`` rejects removed
    API names and known stale claims in README/MkDocs/site examples. The
    production-readiness document still states current limitations explicitly.
41. **Closed in this worktree:** Docstrings now use the enforced Google-style
    section format, duplicated acquisition prose was removed, and comments
    were reviewed so retained historical context explains current invariants.
42. **Closed:** runtime and test code no longer uses `del variable` as an
    unused-variable workaround.

55. **Closed in this worktree:** The README linked to several historical
    uppercase documentation paths that no longer exist, and the security policy
    overstated checkpoint safety by omitting the explicitly gated legacy pickle
    loader. Documentation drift could send users to 404s or cause operators to
    misunderstand the trust boundary.

### P5 — deployed site UX/UI and branding

43. **Closed and deployed:** The palette is over-dependent on saturated purple/indigo gradients, glow,
    glass, and dark backgrounds. It reduces hierarchy and makes the page feel
    like a generic AI landing page rather than a graph/recommendation tool.
44. **Closed and deployed:** The mobile menu is a full-screen sheet with large controls and no visible
    focus trap/focus restoration. In the observed narrow viewport it dominates
    the initial experience and can obscure the primary content.
45. **Closed and deployed:** The desktop/mobile responsive states need explicit breakpoint QA; the live
    page was observed at a narrow viewport with the menu open and a horizontal
    scrollbar visible.
46. **Closed and deployed:** The logo is a low-information radial network mark with a duplicated SVG
    gradient ID (`logoGrad`) rendered in multiple places. Replace it with a
    distinctive, scalable mark that communicates “morel” plus graph/modality
    completion, with stable unique IDs or no ID-dependent paint.
47. **Closed and deployed:** Other inline SVGs reuse IDs such as `perf-line`; duplicate IDs can make
    gradients resolve against the wrong definition. Generate unique IDs or use
    CSS/currentColor paints.
48. **Closed and deployed:** Footer GitHub links concatenate `SITE.repo` with `blob/...` without a slash,
    producing broken URLs such as `github.com/sachncs/morelblob/master/...`.
49. **Closed in this worktree:** The site imports Google Fonts at runtime, adding
    a third-party dependency and a render-blocking network path without a local
    fallback metric or documented privacy/performance decision. The redesign now
    uses the system font stack and has no Google Fonts runtime dependency.
50. **Closed and deployed:** The landing page now
    puts problem → mechanism → proof → quickstart before decorative
    architecture and adoption sections.
51. **Closed and deployed:** Unsupported scaling and
    production claims were removed or qualified; performance cards link to the
    benchmark methodology and readiness evidence, with dataset/configuration
    limitations stated in the copy.
52. **Closed and deployed:** The page exposes the API
    version, test/coverage snapshot, and dated last-verified value from the
    shared `VERIFICATION` source.
53. **Closed and deployed:** Dialog semantics, focus
    trapping/restoration, Escape handling, reduced-motion behavior, contrast,
    and decorative SVG labelling are covered by the local browser and axe
    suite.

## Fix plan

This is the execution plan for the issues that remain after the closed items
above. Each item has an evidence-producing gate; a passing unit test alone is
not sufficient for the production claims.

### Phase 0 — completed foundations

The repository now has a reproducible local environment, a pinned dependency
lock, Python 3.10–3.13 CI, strict Ruff/mypy gates, built-wheel and image audits,
property/boundary tests, frontend/browser/axe checks, generated verification
metrics, fail-closed serving, and the redesigned deployed site. These are
regression gates and must remain green while the open work proceeds.

### Phase 1 — finish the serving error contract

1. Replace the remaining ordinary `except Exception` boundaries in loader,
   HTTP middleware, and recommender execution with a documented taxonomy for
   expected domain, dependency, timeout, cancellation, and programmer errors.
2. Preserve cancellation and process-interrupt semantics; sanitize dependency
   failures into stable 5xx envelopes with correlation IDs and structured
   operator logs.
3. Add fault-injection tests for each taxonomy branch, including factory,
   checkpoint, tensor, network, timeout, and request-cancellation failures.

Evidence: a contract test matrix mapping exception class to HTTP status, public
error code, log fields, and retry/no-retry behavior.

### Phase 2 — complete typed extension architecture

1. Define typed ABC/protocol contracts and capability declarations for every
   pluggable encoder, router, codebook, completer, recommender, and retrieval
   strategy, including optional capabilities currently accessed with `getattr`.
2. Require validators for third-party factory registrations and reject an
   incompatible plugin at registration/startup rather than first request.
3. Document public, semi-private, and private naming; import boundaries;
   deprecation policy; ownership; immutability; and cache invalidation rules.
4. Run every built-in and test plugin through the same contract suite, including
   real pipeline → trainer → checkpoint → serving flows.

Evidence: typed plugin fixtures, registration-time failures, mypy coverage of
the extension surface, and compatibility tests for documented aliases.

### Phase 3 — production capacity and operations

1. Benchmark representative catalog sizes and hardware for retrieval, graph
   encoding, CPU transformer inference, startup warm-up, and concurrent HTTP
   traffic; turn measured p95/p99 budgets into configuration gates.
2. Complete malformed-artifact and broad configuration fuzzing, plus sparse
   graph edge cases across empty, isolated, duplicate, self-loop, zero-modality,
   malformed-shape, and device-transfer inputs.
3. Add a vendor `SecretProvider` adapter seam, exercise external rollback and
   restore procedures, and run alert/metric drillbooks against a deployed
   multi-worker topology.

Evidence: reproducible benchmark artifacts, SLO thresholds in CI/release checks,
fuzz corpus reports, vendor adapter contract tests, and timestamped rollback and
alert drill results.

### Phase 4 — documentation and release closure

1. Keep the issue register, production-readiness page, generated site metrics,
   API examples, and deployment instructions synchronized in one verification
   gate.
2. Verify the deployed Pages route, compatibility redirects, external docs
   hosting, release artifacts, SBOM, and rollback instructions after each
   release.
3. Reassess all “closed” findings at each dependency, Python, runner, or
   frontend major-version upgrade.

### Definition of done

- Fresh install runs the full suite without hidden manual dependencies.
- All quality gates pass in CI, including the site build and link/browser smoke
  tests.
- No endpoint returns fabricated model output when required state is absent.
- Serving metrics contain real latency observations and actionable errors.
- Public contracts, extension points, naming rules, and checkpoint security are
  documented and enforced.
- The deployed site links resolve, claims are traceable to generated evidence,
  the mobile experience is accessible, and the new logo is used consistently.
- The open Phase 1–4 evidence exists for the target deployment environment;
  until then, the system remains audited and hardened but is not declared
  production-ready by default.
