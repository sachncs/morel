# Engineering standards

This document is the maintainability contract for morel. The goal is not to
force every module into a class; the goal is to make ownership, variation, and
failure behavior explicit.

## Python style

- Follow Google-style Python conventions: four-space indentation, `snake_case`
  functions and variables, `PascalCase` classes, and docstrings with Args,
  Returns, Raises, and Examples sections where they add useful information.
- Keep lines at the repository formatter limit and run `ruff format` rather
  than hand-formatting competing styles.
- Use absolute imports within the package. Keep dependency direction flowing
  from domain code toward infrastructure adapters, not the reverse.
- Type all public functions, registry factories, protocol methods, and
  serialized boundaries. `mypy morel/` is a required gate.

## Visibility and naming

Python has no enforced private keyword, so visibility is a naming contract:

- `name`: public API; safe for users and other packages to depend on.
- `_name`: module or class implementation detail; tests should reach it only
  when testing an invariant that cannot be observed through the public API.
- `__name`: use sparingly for name-mangling when subclass collisions would be
  dangerous, not as a general privacy mechanism.
- `NAME`: module-level constant or registry key set, never mutable request
  state.

Semi-private extension points use a leading underscore plus a typed protocol,
for example `_ComponentFactory` or `_score_batch`. They must not be exported
from `__init__.py` or documented as stable user APIs. Public registries must
validate the factory's output at registration time.

## Objects, contracts, and polymorphism

Use composition for the pipeline and small value objects for validated data.
Use a `Protocol` when third-party implementations should participate without
inheritance; use an `ABC` when the package owns the lifecycle and must provide
shared behavior or invariants.

Every pluggable stage must expose a typed contract:

- encoders transform named modality inputs into feature tensors;
- retrieval strategies return bounded, validated item neighborhoods;
- completion models expose deterministic inference and training behavior;
- recommenders expose score and catalog-shape capabilities;
- persistence adapters load and validate immutable artifacts.

Registries select implementations, but callers depend on the protocol rather
than on a string-specific method signature. Optional capabilities must be
declared (`supports_item_features`, `supports_batch_score`, etc.) and checked
when the pipeline is constructed, not discovered after a request fails.

## Reliability and security

- Fail closed when model, graph, feature, or credential state is missing.
- Do not log credentials, raw user payloads, or full model inputs.
- Raise domain errors internally and map them to a stable error envelope at
  the HTTP boundary. Preserve the original exception for structured logs.
- Make ownership explicit: attached arrays are immutable snapshots or carry a
  content/version token that invalidates caches when replaced.
- Derived tensors that are not serialized model state must have an explicit
  owner, content key, invalidation method, and `Module.to`/device-migration
  path; never expose a mutable implementation tuple as the cache contract.
- Treat model updates as transactions: inference must never observe partially
  mutated parameters. Hold the model write lock through mutation and rollback,
  or use a fully isolated copy-on-write state before publishing a new version.
- Checkpoint loading is safe-by-default. Trusted legacy deserialization must
  be isolated and never be reachable from an untrusted request.
- Every request path must have bounded input, timeout/cancellation behavior,
  metrics, and a correlation ID.

## Change and review checklist

Before merging a change, run:

```bash
.venv-audit/bin/python -m pytest -q
.venv-audit/bin/python -m ruff check .
.venv-audit/bin/python -m ruff format --check .
.venv-audit/bin/python -m mypy morel
pnpm --dir site build
```

Changes to public behavior must add contract tests, update the relevant
reference documentation, and state whether the change is backward compatible.
Performance changes need a before/after benchmark at a representative graph
size. Security-sensitive changes need a negative test that proves the unsafe
path remains closed.
