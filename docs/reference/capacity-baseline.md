# Local capacity baseline

This page records a repeatable local signal for capacity planning. It is not a
production SLO: timings depend on hardware, thread settings, dependency
versions, graph shape, model configuration, and query mix.

## Environment

The baseline was captured on 2026-10-15 at commit `02e6917` using the local
`.venv-audit` environment:

| Field | Value |
| --- | --- |
| Platform | macOS 26.7.2, arm64 |
| Python | 3.11.16 |
| NumPy | 2.4.6 |
| SciPy | 1.17.1 |
| PyTorch | 2.14.1 |
| PyTorch threads | 6 |

## Results

Command:

```bash
source .venv-audit/bin/activate
pytest -q benchmarks/forward.py --benchmark-only --benchmark-min-rounds=3 --no-cov
```

The forward benchmark uses a 32-query batch and `visual=16`, `text=8`:

| Scale | Min | Mean | Median | Max |
| --- | ---: | ---: | ---: | ---: |
| 1k items | 207.40 ms | 233.15 ms | 208.21 ms | 283.83 ms |
| 10k items | 6.512 s | 6.920 s | 6.769 s | 7.480 s |

The model-backed serving smoke also passed locally:

```bash
make serve-model-smoke
```

It measured three synthetic recommendation requests at p50 `1.0 ms`, p95
`1.2 ms`, and p99 `1.2 ms` under the default 30-second p95/p99 smoke budgets. This
measures the small bundled smoke model, not a representative production
catalog or hardware deployment.

## Interpretation and follow-up

These results establish a reproducible comparison point, not an acceptance
threshold. Before production use, repeat the same measurements on the target
CPU/GPU, catalog size, modality dimensions, concurrency, and request mix;
then set explicit p95/p99 startup, retrieval, completion, recommendation, and
memory budgets in the release gate. The current repository does not yet have
that deployment-specific calibration.
