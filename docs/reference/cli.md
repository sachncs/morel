# Reference — CLI

morel ships a single ``morel`` console entry point with subcommands
for each lifecycle stage. This page documents every flag.

## Top-level

```
morel [-h] {data,train,eval,bench,reproduce,serve,render-fidelity,render-api} ...
```

A bare ``morel`` (or ``python -m morel``) prints the subcommand tree
and exits 0. Pass ``-h`` or ``--help`` for the full list of options.

## `morel data`

The data lifecycle: download → extract → build → mask → verify.

### `morel data download`

```bash
morel data download [--category CATEGORY] [--dest DIR] [--legacy] [--config CFG]
```

| Flag          | Default | Meaning |
|---------------|---------|---------|
| ``--category``| ``Beauty`` | Which dataset category. |
| ``--dest``    | ``data/raw`` | Output directory. |
| ``--legacy``  | off | Use the legacy mirror (debug only). |
| ``--config``  | (none) | Optional config YAML. |

### `morel data extract`

```bash
morel data extract [--data-dir DIR] [--out-dir DIR] [--config CFG] [--synthetic]
```

Adds ``--synthetic`` to skip model downloads and use the deterministic
random encoder.

### `morel data build`

```bash
morel data build [--data-dir DIR] [--out-dir DIR] [--min-edges N] [--config CFG] [--synthetic]
```

``--min-edges`` overrides ``data.min`` for k-core filtering.

### `morel data mask`

```bash
morel data mask --items N --modalities M [--ratio R] [--kind K] --out FILE [--config CFG]
```

Required: ``--items``, ``--modalities``, ``--out``. The mask is saved
as a ``.npy`` file.

### `morel data verify`

Walks a directory looking for ``*.manifest.json`` sidecars and prints
each path. No flag.

## `morel train`

### `morel train completion`

```bash
morel train completion [--config CFG] [--epochs N] [--items N] [--users N]
```

### `morel train recommendation`

```bash
morel train recommendation [--config CFG] [--epochs N] [--items N] [--users N]
```

## `morel eval`

### `morel eval rank`

```bash
morel eval rank [--config CFG] [--items N] [--users N] [--epochs N]
```

Drives the trained ranker over the test split and reports
``recall@K`` and ``ndcg@K`` for each ``K`` in ``config.eval.ks``.

### `morel eval robustness`

```bash
morel eval robustness [--config CFG] [--items N] [--users N] [--epochs N]
```

Sweeps every ratio in ``config.eval.robustness`` and reports
per-cutoff metrics across the sweep.

### `morel eval ablations`

```bash
morel eval ablations [--config CFG] [--items N] [--users N]
```

Runs the baseline plus each condition in ``config.eval.ablations``
through the same pipeline, changing only the named component.

## `morel bench`

```bash
morel bench [--sizes "16,32"] [--epochs N]
```

Runs the benchmark suite at the requested item scales.

## `morel reproduce`

```bash
morel reproduce CONFIG.yaml [--items N] [--users N] [--epochs N]
```

Loads the saved config and manifest and re-runs the experiment
deterministically.

## `morel serve`

```bash
morel serve [--host HOST] [--port PORT] [--workers N] [--config CFG]
```

Starts the FastAPI inference server. Configuration of rate limits and
auth happens via the env vars documented in
[How-to: serve](../howto/serve.md).

## `morel render-fidelity`

```bash
morel render-fidelity OUT.md [OUT.json]
```

Renders the paper-fidelity registry as Markdown; if ``OUT.json`` is
supplied, a JSON export is written alongside.

## `morel render-api`

```bash
morel render-api [OUT.md]
```

Regenerates the API reference from each module's ``__all__``.
Default output is ``docs/reference/api.md``.

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Success. |
| 1    | Soft error (handled ``Error`` subtype printed to stderr). |
| 2    | Usage error (unknown subcommand, bad flag). |

Anything else is an unexpected exception and surfaces a traceback.
