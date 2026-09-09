# morel — API

The morel API is the union of each package's `__all__`. This page is
machine-generated from the actual `__all__` of every module so it cannot
drift. Regenerate with `morel render-api` (or `python -m
morel.devtools.gen_api`).

## morel

```python
from morel import (
    'Config',
    'Embedding',
    'Manifest',
    'Output',
    'Pipeline',
    'configure_log',
    'logger',
    'seed_everything',
)
```

- `Config` — Top-level morel configuration.
- `Embedding` — Tensor wrapper that exposes shape, dtype, device explicitly.
- `Manifest` — Manifest sidecar for a data artifact.
- `Output` — Pipeline forward output.
- `Pipeline` — End-to-end GRE-MC pipeline.
- `configure_log` — Configure the root morel logger.
- `logger` — Return a child logger (deprecated alias for :func:`logger`).
- `seed_everything` — Seed every RNG in the runtime. Returns the seed used.

## morel.app

```python
from morel.app import (
    'Ablate',
    'Benchmark',
    'Experiment',
    'Rank',
    'Reproduce',
    'Robust',
)
```

- `Ablate` — Run every condition in ``config.eval.ablations`` and compare them.
- `Benchmark` — Run a benchmark sweep and return timings.
- `Experiment` — Top-level experiment orchestration.
- `Rank` — Train the downstream ranker with BPR and write artifacts.
- `Reproduce` — Reproduce a run from a saved config and manifest.
- `Robust` — Robustness sweep over the configured mask ratios.

## morel.codebook

```python
from morel.codebook import (
    'Codebook',
    'KIND',
    'Noop',
    'Soft',
    'VQ',
    'balance',
    'build',
    'usage',
)
```

- `Codebook` — Abstract base class for vector-quantization codebooks.
- `KIND` — dict() -> new empty dictionary
- `Noop` — No-op codebook used for ablations; returns the input and a uniform probs.
- `Soft` — Codebook that uses a Router for the discrete selection.
- `VQ` — Vector-quantizing codebook with straight-through gradient.
- `balance` — Codebook load-balancing loss: ``K * sum_e bar_p_e^2`` per the paper.
- `build` — Build the codebook selected by ``config.codebook.kind``.
- `usage` — KL(bar_p || uniform) codebook usage loss.

## morel.complete

```python
from morel.complete import (
    'Decoders',
    'KIND',
    'build',
)
```

- `Decoders` — One MLP head per modality, with a learned [MASK] token per modality.
- `KIND` — dict() -> new empty dictionary
- `build` — Build the modality completer selected by ``config.complete.kind``.

## morel.core

```python
from morel.core import (
    'Cfg',
    'Cluster',
    'Config',
    'Datum',
    'Determinism',
    'Device',
    'Embedding',
    'Error',
    'FidelityEntry',
    'FidelityStatus',
    'Model',
    'Net',
    'Rate',
    'SeedState',
    'Shape',
    'Train',
    'barrier',
    'checkpoints',
    'cleanup',
    'configure_log',
    'deterministic',
    'device',
    'features',
    'fidelity_all',
    'fidelity_clear',
    'fidelity_register',
    'fidelity_render_json',
    'fidelity_render_markdown',
    'graphs',
    'init',
    'initialized',
    'lead',
    'local',
    'log_metrics',
    'logger',
    'manifest',
    'mean',
    'processed',
    'rank',
    'raw',
    'root',
    'runs',
    'seed_everything',
    'seed_restore',
    'seed_state',
    'size',
    'state',
    'to',
)
```

- `Cfg` — Invalid or inconsistent configuration.
- `Cluster` — Module-level distributed runtime state.
- `Config` — Top-level morel configuration.
- `Datum` — Data acquisition, validation, or loading failures.
- `Determinism` — Reproducibility invariant violated.
- `Device` — Supported device types.
- `Embedding` — Tensor wrapper that exposes shape, dtype, device explicitly.
- `Error` — Base class for every exception raised by morel.
- `FidelityEntry` — One component's fidelity declaration.
- `FidelityStatus`
- `Model` — Model construction, forward, or parameter validation failures.
- `Net` — Graph construction, invariant violation, or retrieval failures.
- `Rate` — Evaluation failures (empty score matrix, etc.).
- `SeedState` — Snapshot of all RNG state in the runtime.
- `Shape` — Tensor shape mismatch.
- `Train` — Training loop failures (NaN loss, missing checkpoint, etc.).
- `barrier` — Block until all ranks reach this point.
- `checkpoints` — Return the checkpoints directory for a run.
- `cleanup` — Destroy the default process group if initialised.
- `configure_log` — Configure the root morel logger.
- `deterministic` — Seed every RNG for the duration of the block, then restore prior state.
- `device` — Resolve a torch device.
- `features` — Return the features directory for a dataset.
- `fidelity_all` — Return all registered entries sorted by name.
- `fidelity_clear` — Clear the registry. Used by tests.
- `fidelity_register` — Register a fidelity entry. Use as a decorator.
- `fidelity_render_json` — Render the registry as a JSON file.
- `fidelity_render_markdown` — Render the registry as a Markdown report.
- `graphs` — Return the graphs directory for a dataset.
- `init` — Initialize the default process group.
- `initialized` — Return whether the runtime has been initialised.
- `lead` — Return True for the rank-zero process (always True when single-process).
- `local` — Return the local rank on the current node.
- `log_metrics` — Append a JSONL line of metrics to ``<directory>/metrics.jsonl``.
- `logger` — Return a child logger (deprecated alias for :func:`logger`).
- `manifest` — Return the manifest sidecar path for an artifact.
- `mean` — All-reduce a scalar across ranks and return its mean.
- `processed` — Return the processed data directory for a given dataset name.
- `rank` — Return the global rank of the current process (0 when single-process).
- `raw` — Return the raw data directory.
- `root` — Return the morel data root directory.
- `runs` — Return the run-artifact directory.
- `seed_everything` — Seed every RNG in the runtime. Returns the seed used.
- `seed_restore` — Restore the RNG state from a snapshot.
- `seed_state` — Snapshot the current RNG state of every library.
- `size` — Return the world size (1 when single-process).
- `state` — Module-level distributed runtime state.
- `to` — Move a tensor to the target device.

## morel.data

```python
from morel.data import (
    'EXTRACTORS',
    'Feature',
    'MASKS',
    'Manifest',
    'Mask',
    'Random',
    'Sentence',
    'Vision',
    'assemble',
    'bernoulli',
    'bipartite',
    'block',
    'build_mask',
    'check',
    'checksum',
    'confirmed',
    'cooc',
    'cooccurrence',
    'download',
    'features',
    'fetch',
    'fingerprint',
    'graph',
    'interactions',
    'kcore',
    'load_graph',
    'load_manifest',
    'load_npz',
    'manifest_path',
    'random',
    'review',
    'save_graph',
    'save_manifest',
    'stack',
    'store',
    'stream',
    'structured',
    'text',
    'validate_interactions',
    'visual',
)
```

- `EXTRACTORS` — dict() -> new empty dictionary
- `Feature` — One feature extractor for raw modality inputs.
- `MASKS` — dict() -> new empty dictionary
- `Manifest` — Manifest sidecar for a data artifact.
- `Mask` — Immutable mask value object with the Mask Protocol.
- `Random` — Deterministic pseudo-random encoder.
- `Sentence` — Text encoder backed by sentence-transformers.
- `Vision` — Visual encoder backed by a torchvision classification backbone.
- `assemble` — Build the feature encoder selected by ``config.encoder.{text,visual}``.
- `bernoulli` — Independent Bernoulli masking with at-least-one repair.
- `bipartite` — Build a user-item bipartite adjacency matrix.
- `block` — Block masking: contiguous modality spans are masked together.
- `build_mask` — Build the masking strategy selected by ``config.masking.kind``.
- `check` — Validate a modality availability mask.
- `checksum` — Compute SHA256 of a file's contents.
- `confirmed` — Two-pass exact k-core streaming loader.
- `cooc` — Build an item co-occurrence graph from a stream of bipartite chunks.
- `cooccurrence` — Build an item-item co-occurrence graph from a user-item bipartite.
- `download` — Download Amazon 5-core review and metadata for a category.
- `features` — Validate per-modality feature arrays.
- `fetch` — Fetch a remote URL to a local file with retries and optional checksum.
- `fingerprint` — Stable SHA256 of an array's bytes (used for manifest binding).
- `graph` — Validate a sparse graph adjacency.
- `interactions` — Stream Amazon reviews into a filtered bipartite graph.
- `kcore` — Peel nodes below ``min_edges`` until stable.
- `load_graph` — Load a sparse graph and verify its manifest.
- `load_manifest` — Load a manifest sidecar.
- `load_npz` — Load a ``.npz`` artifact and verify the manifest if present.
- `manifest_path` — Return the sidecar manifest path for an artifact.
- `random` — Deterministic random L2-normalized features.
- `review` — Yield chunks of JSON-decoded records from an Amazon review file.
- `save_graph` — Atomically save a sparse graph with manifest.
- `save_manifest` — Atomically save a manifest next to an artifact.
- `stack` — Stack a list of masks into a 3-D array ``(len(masks), items, modalities)``.
- `store` — Atomically save one or more numpy arrays plus an optional manifest.
- `stream` — Yield ``(user_ids_chunk, item_ids_chunk)`` for an Amazon review file.
- `structured` — Use a fixed pattern (e.g. ground-truth modality availability) as the mask.
- `text` — Encode text inputs through any Feature implementation.
- `validate_interactions` — Validate a user-item interaction pair array.
- `visual` — Encode image paths through any Feature implementation.

## morel.encode

```python
from morel.encode import (
    'Attention',
    'Baseline',
    'CLS',
    'Enc',
    'Identity',
    'Input',
    'KIND',
    'Layer',
    'Mean',
    'Sum',
    'Token',
    'Transformer',
    'build',
)
```

- `Attention` — Scaled dot-product attention pooling over a sequence dim.
- `Baseline` — Multiplexer that builds the requested graph encoder.
- `CLS` — Alias for Token pooling.
- `Enc` — Graph encoder turns modality features into a hidden embedding.
- `Identity` — A trivial encoder that just projects concatenated features with a Linear.
- `Input` — Concatenate per-modality features (zero-pad missing) with PE, then project.
- `KIND` — dict() -> new empty dictionary
- `Layer` — A single Pre-LN transformer block: MHA + FFN with residuals.
- `Mean` — Mean pool over a sequence dim, masking invalid tokens.
- `Sum` — A summation encoder (no learnable projection).
- `Token` — Select the first token (CLS-like) of every sequence.
- `Transformer` — L-layer graph transformer with query-pool aggregation.
- `build` — Build the joint encoder selected by ``config.encode.kind``.

## morel.eval

```python
from morel.eval import (
    'ABLATIONS',
    'BASELINE',
    'Robust',
    'ablate',
    'conditions',
    'map',
    'modal',
    'mrr',
    'mse',
    'ndcg',
    'precision',
    'recall',
    'results',
    'sweep',
    'variance',
)
```

- `ABLATIONS` — dict() -> new empty dictionary
- `BASELINE` — str(object='') -> str
- `Robust` — Result of a robustness sweep.
- `ablate` — Return ``config`` with the named ablation applied.
- `conditions` — Return the sweep's condition names: the baseline then each ablation.
- `map` — Mean Average Precision@K.
- `modal` — Per-modality mean squared error.
- `mrr` — Mean reciprocal rank of the first relevant item.
- `mse` — Mean squared error.
- `ndcg` — Mean NDCG@K.
- `precision` — Mean Precision@K.
- `recall` — Mean Recall@K across users with at least one relevant item.
- `results` — Evaluate a single metric across ablation conditions.
- `sweep` — Evaluate a metric across a range of mask ratios.
- `variance` — Explained variance score in ``(-inf, 1]``.

## morel.graph

```python
from morel.graph import (
    'Bipartite',
    'Item',
    'Laplace',
    'Subgraph',
    'connected',
    'laplacian',
    'pe',
)
```

- `Bipartite` — Immutable user-item bipartite graph.
- `Item` — Symmetric item-item co-occurrence graph.
- `Laplace` — Caching bottom-k Laplacian PE module.
- `Subgraph` — A node-subset view of an Item graph.
- `connected` — Return True if the subgraph nodes form a connected subgraph.
- `laplacian` — Symmetric normalized Laplacian: L = I - D^{-1/2} A D^{-1/2}.
- `pe` — Compute the bottom-k nontrivial Laplacian PE.

## morel.pipeline

```python
from morel.pipeline import (
    'Output',
    'Pipeline',
    'mode',
)
```

- `Output` — Pipeline forward output.
- `Pipeline` — End-to-end GRE-MC pipeline.
- `mode` — Run a block with ``module`` in the given train/eval mode, then restore.

## morel.recommend

```python
from morel.recommend import (
    'KIND',
    'Light',
    'MF',
    'Pop',
    'Recommender',
    'bpr',
    'build',
    'distinct',
    'negatives',
    'to_ranks',
)
```

- `KIND` — dict() -> new empty dictionary
- `Light` — LightGCN: linear message passing with mean aggregation.
- `MF` — Matrix factorization with dot-product scoring.
- `Pop` — Popularity baseline: scores proportional to item interaction count.
- `Recommender` — One downstream ranker.
- `bpr` — Bayesian Personalized Ranking loss.
- `build` — Build the downstream ranker selected by ``config.recommend.kind``.
- `distinct` — Draw ``size`` distinct integers from ``[0, high)``.
- `negatives` — Sample ``count`` distinct negatives per user.
- `to_ranks` — Map ranks over the *negative* items back to actual item ids.

## morel.retrieve

```python
from morel.retrieve import (
    'KIND',
    'Result',
    'acs',
    'acs_batch',
    'anchor',
    'anchor_batch',
    'batch',
    'bfs',
    'cast',
    'mage',
    'mage_batch',
    'neighbors_map',
    'path',
    'rel',
    'relevance',
    'retrieve',
    'walk',
)
```

- `KIND` — dict() -> new empty dictionary
- `Result` — Retrieval output for one query or a batch.
- `acs` — Compute the Anchor Connecting Subgraph.
- `acs_batch` — Compute ACS for a batch of anchor sets.
- `anchor` — Top-k cosine neighbors of ``query_item`` in the given modality.
- `anchor_batch` — Anchor retrieval for a batch of query items.
- `batch` — Batched retrieval that returns padded tensors for downstream models.
- `bfs` — Multi-source BFS.
- `cast` — Convert a batched Result into (nodes, mask, sizes) torch tensors.
- `mage` — Run MAGE greedy expansion.
- `mage_batch` — Run MAGE for a batch of queries and anchor sets.
- `neighbors_map` — Precompute neighbor arrays for every node.
- `path` — Return a shortest path from ``start`` to ``end``.
- `rel` — Mean of r(i, v) over ``nodes``, excluding the query.
- `relevance` — Cosine relevance r(i, v) over jointly observed modalities.
- `retrieve` — Retrieve and expand a subgraph for one query item.
- `walk` — Iterate over the neighbors of ``node``.

## morel.route

```python
from morel.route import (
    'Dense',
    'Fixed',
    'Gumbel',
    'KIND',
    'Router',
    'Top',
    'Weights',
    'build',
)
```

- `Dense` — Plain softmax routing over K entries.
- `Fixed` — A non-trainable router that returns a uniform distribution.
- `Gumbel` — Pure Gumbel-Softmax router (no top-k sparsification).
- `KIND` — dict() -> new empty dictionary
- `Router` — Protocol-style base for routers (kept as nn.Module so parameters register).
- `Top` — Top-P (top-K) sparsifying router.
- `Weights` — Routing distribution and any associated metadata.
- `build` — Build a router by name.

## morel.serve

```python
from morel.serve import (
    'Ask',
    'Default',
    'Done',
    'Event',
    'Fill',
    'Health',
    'List',
    'Loader',
    'Outcome',
    'Pick',
    'Query',
    'RWLock',
    'Read',
    'Rollback',
    'Scope',
    'Signal',
    'Stats',
    'Step',
    'Tell',
    'Updater',
    'Write',
    'admin',
    'assert_',
    'create',
    'dependency',
    'reader',
    'serialize',
    'token',
    'viewer',
    'writer',
)
```

- `Ask` — One feedback event submitted by a client.
- `Default` — No-training loss step used as a baseline and for tests.
- `Done` — Response containing the completed modalities per item.
- `Event` — One user-feedback event.
- `Fill` — Request to complete missing modalities for a set of items.
- `Health` — Health probe response.
- `List` — Response with ranked items for the requested user.
- `Loader` — Cache of named model pipelines keyed by their checkpoint path.
- `Outcome` — Result of one update tick.
- `Pick` — One (item, score) pair.
- `Query` — Request to score a user against the catalogue.
- `RWLock` — A reader-writer lock with writer preference.
- `Read` — Context manager returned by :meth:`RWLock.read`.
- `Rollback` — Response from /v1/rollback.
- `Scope`
- `Signal` — str(object='') -> str
- `Stats` — Response from /v1/stats.
- `Step` — Compute the loss for one update step given a batch of feedback.
- `Tell` — Response from /v1/feedback.
- `Updater` — Background updater that calls :meth:`tick` periodically.
- `Write` — Context manager returned by :meth:`RWLock.write`.
- `admin` — Return whether admin-scope auth is configured.
- `assert_` — Raise if a deployment attempted to enable auth without setting any token.
- `create` — Create a FastAPI app.
- `dependency` — Return a FastAPI-compatible dependency callable for the given scope.
- `reader` — Context manager for a read lock.
- `serialize` — Convert torch tensors to nested Python lists for JSON serialization.
- `token` — Return the configured token for ``scope``, or ``None`` if auth is off.
- `viewer` — Return whether read-scope auth is configured.
- `writer` — Context manager for a write lock.

## morel.train

```python
from morel.train import (
    'BPR',
    'Completion',
    'Composite',
    'Fit',
    'Loss',
    'Monitor',
    'Rec',
    'Recommendation',
    'Reconstruction',
    'State',
    'Trainer',
    'ce',
    'hash_config',
)
```

- `BPR` — BPR loss using provided positive/negative scores.
- `Completion` — Trainer for modality completion.
- `Composite` — Linear combination of named loss components.
- `Fit` — Configuration for completion training.
- `Loss` — A training loss.
- `Monitor` — Append ``(time, **metrics)`` lines to ``metrics.jsonl``.
- `Rec` — Configuration for recommendation training.
- `Recommendation` — BPR trainer with pre-sampled strict negatives and item-only scoring.
- `Reconstruction` — Masked MSE reconstruction normalized by missing elements per modality.
- `State` — Trainer state snapshot for resume.
- `Trainer` — Abstract training loop.
- `ce` — Cross-entropy helper used by codebook-style losses.
- `hash_config` — Stable SHA256 cfg_hash of a configuration object's public attributes.
