# Getting started with morel

This guide takes you from `pip install` to a working end-to-end run
on synthetic data in five minutes. If you want to use real Amazon
Reviews data instead, jump to [Tutorial 2 — real Amazon data](tutorials/real-data.md).

## Before you start

You need Python 3.10 or newer. Confirm with:

```bash
python3 --version
```

The output should start with `3.10`, `3.11`, `3.12`, or `3.13`.

!!! tip
    Use a virtual environment so the install doesn't pollute your
    global Python.

## Install

=== "From source (recommended)"

    ```bash
    git clone https://github.com/sachncs/morel.git
    cd morel
    python3 -m venv .venv
    source .venv/bin/activate          # macOS / Linux
    # .venv\Scripts\activate           # Windows PowerShell

    pip install -e '.[dev]'
    ```

    The `.[dev]` extra pulls in pytest, ruff, mypy, mkdocs and the rest of
    the developer tooling.

=== "Inference server too"

    ```bash
    pip install -e '.[dev,serve]'
    ```

    Adds FastAPI, uvicorn, prometheus-client, and httpx.

=== "Docker"

    ```bash
    docker compose up --build
    ```

    The image starts the inference service on port `8080` with
    `HEALTHCHECK` on `/health`.

## Minimal example — synthetic data

The fastest demo doesn't need any dataset. It builds a 20-user /
50-item synthetic graph, masks 40 % of modalities, runs the completion
stage, and prints ranking metrics — a few seconds of work.

```bash
python examples/demo.py
```

Expected output (numbers are deterministic for the shipped seed):

```
Reconstructed visual shape: (50, 16)
Routing weights shape: (50, 100)
Score matrix shape: (20, 50)
  recall@10: 0.6908
  ndcg@10: 0.6755
```

If that worked, morel is installed and the pipeline runs end-to-end.
[`examples/demo.py`](https://github.com/sachncs/morel/blob/master/examples/demo.py)
is the recommended starting point for exploring the package
interactively — its steps map directly to the
[method walkthrough](concepts/method.md).

## Minimal Python example

You can drive the same flow from the Python API. The shortest valid
end-to-end call looks like this:

```python
import numpy as np
import torch

from morel import Config, Pipeline
from morel.data.build import bipartite, item_cooccurrence
from morel.data.mask import bernoulli
from morel.recommend import Light

rng = np.random.default_rng(0)
users, items = 20, 50

# Synthetic interactions.
ui = bipartite(
    rng.integers(0, users, size=200),
    rng.integers(0, items, size=200),
    users, items,
)

# Per-item features with 40% of modalities masked out.
features = {
    "visual": rng.normal(size=(items, 16)).astype(np.float32),
    "text": rng.normal(size=(items, 8)).astype(np.float32),
}
mask = bernoulli(items, 2, 0.4, seed=42).to_numpy()

# Build the GRE-MC pipeline and attach the corpus.
pipeline = Pipeline(Config(), dims={"visual": 16, "text": 8})
pipeline.attach_corpus(features, mask, item_cooccurrence(ui))

# Complete the missing modalities and score users.
output = pipeline(
    {k: torch.from_numpy(v) for k, v in features.items()},
    torch.from_numpy(mask),
    item_cooccurrence(ui),
    index=torch.arange(items),
    training=False,
)

scores = Light(users=users, items=items, embed=32, layers=2)(
    torch.arange(users), torch.arange(items), ui
)
print("completed visual:", output.completed["visual"].shape)
print("routing weights:", output.routing.shape)
print("score matrix:", scores.shape)
```

This walks every stage: build the graph, complete the missing
modalities, route through the codebook, and rank.

## Train the full pipeline (CLI)

The `morel` console command covers every lifecycle stage. The
relevant top-level subcommands:

```bash
python -m morel --help
```

A few starting points:

| Command | Purpose |
|---|---|
| `python -m morel data extract --synthetic` | Build a synthetic feature corpus. |
| `python -m morel train completion` | Train the completion stage. |
| `python -m morel train recommendation` | Train the ranker. |
| `python -m morel eval rank` | Evaluate the trained ranker. |
| `python -m morel eval robustness` | Sweep across missing-modality ratios. |
| `python -m morel serve --port 8080` | Start the inference API. |
| `python -m morel render-fidelity docs/reference/fidelity.md` | Render the paper-fidelity report. |
| `python -m morel render-api docs/reference/api.md` | Regenerate the API reference. |

Each subcommand supports `--help` for its own flags.

## Verify the install

Run the smoke test that ships with the repo:

```bash
python -m pytest tests/unit -x
```

The full suite (482 tests, 80.55 % coverage at the time of writing)
takes about a minute on a workstation and is what CI runs on every
push.

## Where to go next

- **[Tutorial 1 — synthetic](tutorials/synthetic.md)** — what the
  demo does, step by step.
- **[Tutorial 2 — real Amazon data](tutorials/real-data.md)** —
  download a real dataset and run a full reproduction.
- **[Tutorial 3 — serve over HTTP](tutorials/serve.md)** — wire the
  trained pipeline behind the FastAPI server.
- **[How-to: configure morel](howto/configure.md)** — every config
  field with a plain-English explanation.
- **[Docs hub](docs-hub.md)** — one-page map of every section plus
  role-based reading paths.

!!! tip "Need a quick reference?"
    The home page has the same five-minute walkthrough as a
    one-stop scroll: [Home](index.md).
