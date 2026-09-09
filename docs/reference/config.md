# Reference — config

Every field in the ``Config`` dataclass tree, with its meaning and
the kind of validation it receives at construction time.

## Top-level

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``seed``   | ``int`` | ``42`` | Global seed for torch, numpy, Python random, ``PYTHONHASHSEED``, cuDNN. |
| ``device`` | ``str`` | ``"auto"`` | ``"cpu"``, ``"cuda"``, or ``"auto"``. |

## `data`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``raw``       | ``str`` | ``"data/raw"`` | Path to raw dataset directory. |
| ``processed`` | ``str`` | ``"data/processed"`` | Path to processed dataset directory. |
| ``category``  | ``str`` | ``"Beauty"`` | Dataset category (e.g. ``"Beauty"``). |
| ``min``       | ``int`` | ``5`` | K-core minimum edges per user/item. |

## `encoder`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``text``       | ``str`` | ``"sentence-transformers/all-MiniLM-L6-v2"`` | Text backbone. |
| ``visual``     | ``str`` | ``"resnet50"`` | Visual backbone. |
| ``td``         | ``int`` | ``384`` | Text feature dimension. |
| ``visual_dim`` | ``int`` | ``2048`` | Visual feature dimension. |
| ``batch``      | ``int`` | ``64`` | Encoding batch size. |

## `masking`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind``  | ``str``   | ``"bernoulli"`` | Masking strategy (bernoulli, block). |
| ``ratio`` | ``float`` | ``0.4`` | Fraction of modalities to mask. Must be in ``[0, 1]``. |
| ``seed``  | ``int``   | ``42`` | Per-mask RNG seed. |

## `retrieve`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind``    | ``str`` | ``"mage"`` | Retrieval strategy (mage, anchor, acs, bfs, none). |
| ``anchors`` | ``int`` | ``10``    | Number of anchor nodes per query. |
| ``iters``   | ``int`` | ``10``    | Number of expansion iterations. |

## `encode`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind``    | ``str``   | ``"transformer"`` | Encoder kind. |
| ``hidden``  | ``int``   | ``128`` | Hidden dimension. Must be positive. |
| ``layers``  | ``int``   | ``2``   | Number of encoder layers. |
| ``heads``   | ``int``   | ``4``   | Attention heads. |
| ``dropout`` | ``float`` | ``0.5`` | Dropout rate. |
| ``pe``      | ``int``   | ``20``  | Laplacian positional-encoding width. |

## `route`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind`` | ``str``   | ``"top"`` | Soft-routing strategy (top, dense, gumbel, fixed). |
| ``p``    | ``int``   | ``4`` | Top-p or number of entries. Must be positive. |
| ``tau``  | ``float`` | ``0.5`` | Softmax temperature. |

## `codebook`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind`` | ``str`` | ``"gumbel"`` | Codebook kind (gumbel, vq, identity). |
| ``size`` | ``int`` | ``100`` | Codebook size. Must be positive. |

## `complete`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind``   | ``str`` | ``"mlp"`` | Completer kind. |
| ``hidden`` | ``int`` | ``128`` | Hidden dimension. |

## `recommend`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``kind``  | ``str`` | ``"light"`` | Downstream ranker (light, mf, pop). |
| ``embed`` | ``int`` | ``64`` | Embedding width. |
| ``layers`` | ``int`` | ``3`` | GCN layers. |

## `completion` / `recommendation`

Training-loop hyperparameters. The ``*val`` fields must be in
``[0, 1]``; the other integer fields are unbounded; ``grad_clip`` is
``float`` and clamps gradient norm.

| Field | Default (completion) | Default (recommendation) | Meaning |
|-------|---------------------|---------------------------|---------|
| ``epochs``       | ``100``  | ``100``  | Number of training epochs. |
| ``batch``        | ``512``  | ``1024`` | Mini-batch size. |
| ``lr``           | ``1e-3`` | ``1e-3`` | Learning rate. |
| ``weight_decay`` | ``1e-5`` | ``1e-5`` | Adam weight decay. |
| ``usage``        | ``1.0``  | n/a      | Usage-loss weight (completion only). |
| ``balance``      | ``1.0``  | n/a      | Balance-loss weight (completion only). |
| ``grad_clip``    | ``1.0``  | ``1.0``  | Gradient-norm clip. |
| ``val``          | ``0.1``  | ``0.1``  | Validation fraction. Must be in ``[0, 1]``. |
| ``patience``     | ``10``   | ``10``   | Early-stopping patience. |
| ``amp``          | ``False``| ``False``| Mixed-precision toggle. |
| ``negatives``    | n/a      | ``1``    | Negatives per positive (recommendation only). |

## `eval`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``ks``         | ``tuple[int, ...]``     | ``(10, 20)`` | K values for ranking metrics. Each must be positive. |
| ``robustness`` | ``tuple[float, ...]``   | ``(0.1..0.9)`` | Mask ratios for the robustness sweep. |
| ``ablations``  | ``tuple[str, ...]``     | ``(noretry, nope, nobook)`` | Registered ablation condition names. |

## `serve`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``host``    | ``str``  | ``"0.0.0.0"`` | Bind host. |
| ``port``    | ``int``  | ``8080`` | Bind port. |
| ``workers`` | ``int``  | ``1`` | Number of uvicorn workers. |
| ``auth``    | ``bool`` | ``False`` | Whether auth is enabled (read-only; configure via env vars). |

## `log`

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| ``level``     | ``str``  | ``"INFO"`` | Log level. |
| ``structured``| ``bool`` | ``True`` | Emit JSON instead of plain text. |
| ``directory`` | ``str``  | ``"runs"`` | JSONL files directory. |

## Validation

``Config.__post_init__`` calls ``validate()`` on every construction
path: ``Config()``, ``Config.defaults()``, ``Config.from_dict``,
``Config.load``, ``Config.env``, and inline ``Config(**kwargs)``
inside notebooks and tests. A field out of range raises ``Cfg``
immediately, not downstream.

## Saving

```python
config.save("configs/my.yaml")
```

``save`` writes the YAML round-trip; ``Config.load`` of the saved
file reproduces the same ``cfg_hash``, which is what the manifest
sidecar binds to.
