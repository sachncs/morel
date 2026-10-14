# morel — Benchmarks

Benchmarks use `pytest-benchmark`. Run with:

```bash
pytest benchmarks/ --benchmark-only --no-cov --benchmark-min-rounds=20 --benchmark-autosave
```

## Suites

- `benchmarks/forward.py` — forward-pass latency for the encoder + codebook
  + decoder at scales `[1k, 10k, 100k]` items.
- `benchmarks/dataset.py` — full k-core + graph construction end-to-end.
- `benchmarks/retrieve.py` — anchor + ACS + MAGE throughput.
- `benchmarks/train.py` — completion training epoch on a 50k-item synthetic
  dataset.

## Threshold

The benchmark suite is an opt-in local gate. Record the machine, dependency
lock, dataset scale, and command alongside results; do not compare timings
across unlike hardware. CI validates the benchmark code and package gates,
but does not claim a universal latency budget.
