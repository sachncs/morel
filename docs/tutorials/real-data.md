# Tutorial 2 — train on real Amazon Reviews data

This tutorial downloads a small Amazon Reviews subset, runs the data
lifecycle end-to-end, trains the completion and recommendation
stages, and reports ranking metrics. Allow about an hour on a
single CPU.

## Prerequisites

- A working `pip install -e '.[dev,serve]'` from
  [Getting started](../getting-started.md).
- About 2 GB of free disk for the Amazon Beauty 5-core subset.
- (Optional) CUDA-capable GPU if you want sub-hour training. The
  scripts run on CPU by default.

## Step 1 — download the data

```bash
python -m morel data download --category Beauty --dest data/raw
```

This pulls the Amazon Reviews 5-core Beauty subset via HTTPS into
`data/raw/`. The download is verified against the manifest's SHA256
when one is provided; otherwise the URL's signing path is logged for
auditing.

If you have a pre-downloaded archive, point `--dest` at the
directory that contains the `.json` review files and skip the
download step.

## Step 2 — extract features

```bash
python -m morel data extract --data-dir data/raw --out-dir data/processed
```

This runs the configured text and visual encoders
(`sentence-transformers/all-MiniLM-L6-v2` for text, `resnet50` for
visual) and writes a `features.npz` plus its `.manifest.json` sidecar
into `data/processed/`. Each modality takes a few minutes; rerun with
`--synthetic` to skip the model downloads during development.

## Step 3 — build the user–item and item–item graphs

```bash
python -m morel data build --data-dir data/raw --out-dir data/processed --min-edges 5
```

Iterative k-core filtering drops users and items below five
interactions; the surviving graph is written as `bipartite.npz` and
`item_graph.npz`, each with a `.manifest.json` sidecar.

Verify the build:

```bash
ls data/processed/*.manifest.json
# bipartite.npz.manifest.json
# features.npz.manifest.json
# item_graph.npz.manifest.json
```

## Step 4 — generate (or accept) a modality mask

Generate a Bernoulli mask once and persist it as the canonical
availability record:

```bash
python -m morel data mask \
    --items $(python -c "import numpy as np; print(np.load('data/processed/features.npz')['visual'].shape[0])") \
    --modalities 2 \
    --ratio 0.4 \
    --kind bernoulli \
    --out data/processed/mask.npy
```

The `--ratio` matches `Config.masking.ratio`; pass a lower value to
make robustness sweeps harder, a higher value to make them easier.

## Step 5 — train the completion stage

```bash
python -m morel train completion --config configs/amazon_beauty.yaml
```

The trainer reads the config, builds the pipeline under the
configured completion hyperparameters, trains for
`config.completion.epochs` epochs with early stopping at
`config.completion.patience`, and writes `runs/<timestamp>/` with
`config.yaml`, `manifest.json`, `metrics.jsonl`, `checkpoints/`, and
the rendered `FIDELITY.md` / `FIDELITY.json` registry.

A minimal config for the Beauty split lives at
`configs/synthetic.yaml` and can be copied as a starting point.

## Step 6 — train the ranker

```bash
python -m morel train recommendation --config configs/amazon_beauty.yaml
```

Same directory layout; the manifest records the configured
recommender so a rerun is bit-identical.

## Step 7 — evaluate

```bash
python -m morel eval rank --config configs/amazon_beauty.yaml --items 12101 --users 22363
```

Adjust `--items` and `--users` to match the post-k-core counts
printed in step 5's `report.md`. The command scores every user
against every item, reports `recall@K` and `ndcg@K` for each `K` in
`config.eval.ks`, and writes a fresh metrics file under
`runs/rank/`.

Run the robustness sweep too:

```bash
python -m morel eval robustness --config configs/amazon_beauty.yaml
```

This runs the trainer across every ratio in
`config.eval.robustness` and reports how each metric responds to
missing-modality pressure.

## Step 8 — rerun from the manifest

Every run writes a `manifest.json` next to its `config.yaml`. To
verify reproducibility:

```bash
python -m morel reproduce runs/<timestamp>/config.yaml \
    --items $(python -c "import numpy as np; print(np.load('data/processed/features.npz')['visual'].shape[0])") \
    --users 22363 \
    --epochs 5
```

The `Reproduce` service binds on the same seed and config hash, so a
successful rerun produces a `metrics.jsonl` with the same line-by-line
loss as the original (modulo non-deterministic GPU kernels).

## Next steps

- [Tutorial: serve over HTTP](serve.md) — wrap the trained
  recommender in the FastAPI server.
- [Operations: serve in production](../operations/deploy.md) —
  Dockerfile, docker-compose, and a Kubernetes skeleton.
