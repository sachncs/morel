# Tutorial 1 — the synthetic pipeline

morel ships with a synthetic-graph demo so you can verify your install
and learn the API without downloading a dataset.

## Run the demo

```bash
python examples/demo.py
```

The script builds a 20-user / 50-item synthetic graph, masks 40% of
modalities, runs the completion stage, and prints ranking metrics.
Total runtime is a few seconds.

## What the demo does, step by step

The same flow that `examples/demo.py` runs is a useful reference for
how morel fits together. Each numbered section maps to a function in
the demo.

### 1. Build a synthetic bipartite graph

```python
import numpy as np
from morel.data.build import bipartite

rng = np.random.default_rng(0)
users, items = 20, 50
ui = bipartite(
    rng.integers(0, users, size=200),
    rng.integers(0, items, size=200),
    users, items,
)
```

`bipartite()` builds a sparse CSR matrix of shape `(users, items)`
where every entry is the count of (user, item) interactions.

### 2. Build per-item features and a mask

```python
features = {
    "visual": rng.normal(size=(items, 16)).astype(np.float32),
    "text": rng.normal(size=(items, 8)).astype(np.float32),
}
mask = bernoulli(items, 2, 0.4, seed=42).to_numpy()
```

Two modalities per item (`visual` is 16-dim, `text` is 8-dim). 40% of
the `items × modalities` cells are zeroed out to simulate missing
data.

### 3. Build the item co-occurrence graph

```python
from morel.data.build import item_cooccurrence

adjacency = item_cooccurrence(ui)
```

This returns the symmetric item–item adjacency `sign(Uᵀ U)` with
self-loops removed. morel's retrieval stage uses this graph to find
context for each query item.

### 4. Construct the pipeline

```python
from morel import Config, Pipeline

pipeline = Pipeline(Config(), dims={"visual": 16, "text": 8})
pipeline.attach_corpus(features, mask, adjacency)
```

The pipeline is the orchestrator. `attach_corpus` registers the
feature tensors, mask, and adjacency with the pipeline so every
later forward call can find them.

### 5. Complete the missing modalities

```python
import torch

output = pipeline(
    {k: torch.from_numpy(v) for k, v in features.items()},
    torch.from_numpy(mask),
    adjacency,
    index=torch.arange(items),
    training=False,
)
```

`pipeline(..., training=False)` switches the model into eval mode for
the call. `output.completed` is a `dict[modality_name, tensor]` with
the reconstructed feature vectors, and `output.routing` is the
soft routing over the codebook.

### 6. Rank users against items

```python
from morel.recommend import Light

scores = Light(users=users, items=items, embed=32, layers=2)(
    torch.arange(users), torch.arange(items), ui
)
```

The ranker is the LightGCN-style recommender from the paper. The
matrix is `(users, items)`; take the top-K entries per row to get
recommendations.

## Inspect the outputs

```python
print("completed visual:", output.completed["visual"].shape)
# torch.Size([50, 16])
print("routing weights:", output.routing.shape)
# torch.Size([50, 100])
print("score matrix:", scores.shape)
# torch.Size([20, 50])
```

Compare these against the demo's expected output to confirm the
install is wired correctly.

## Next steps

- [Tutorial: real Amazon Reviews data](real-data.md) — replace the
  synthetic features with a real dataset.
- [How-to: configure morel](../howto/configure.md) — change a dimension,
  swap a stage, or pin the seed.
