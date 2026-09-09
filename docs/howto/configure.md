# How to configure morel

morel's configuration is a tree of frozen dataclasses. You build it
once from a YAML file or programmatically, then pass the result to
`Pipeline`, `Experiment`, or the CLI.

## The configuration tree at a glance

```
Config
├── seed                 global RNG seed
├── device               "cpu" | "cuda" | "auto"
├── data                 raw/processed paths, category, k-core min
├── encoder              text + visual model names
├── masking              kind, ratio, per-mask seed
├── retrieve             strategy (mage, anchor, bfs, acs, none)
├── encode               joint encoder (kind, hidden, layers, heads, dropout, pe)
├── route                router (kind, p, tau)
├── codebook             VQ / Gumbel-VQ (kind, size)
├── complete             modality completer (kind, hidden)
├── recommend            downstream ranker (kind, embed, layers)
├── completion           completion training loop (epochs, batch, lr, ...)
├── recommendation       recommendation training loop (epochs, batch, ...)
├── eval                 ks, robustness sweep, ablation condition names
├── serve                host/port/workers
└── log                  level, structured flag, output directory
```

Every section is validated at construction time, so a field out of
range (`masking.ratio = 2.0`) raises `Cfg` immediately rather than
producing silently broken state.

## Build a config

### From a YAML file

`configs/synthetic.yaml`:

```yaml
seed: 42
device: cpu
data:
  raw: data/raw
  processed: data/processed
  category: Beauty
  min: 5
encoder:
  text: sentence-transformers/all-MiniLM-L6-v2
  visual: resnet50
  td: 384
  visual_dim: 2048
masking:
  kind: bernoulli
  ratio: 0.4
retrieve:
  kind: mage
  anchors: 10
  iters: 10
encode:
  kind: transformer
  hidden: 128
  layers: 2
  heads: 4
  dropout: 0.5
  pe: 20
route:
  kind: top
  p: 4
  tau: 0.5
codebook:
  kind: gumbel
  size: 100
complete:
  kind: mlp
  hidden: 128
recommend:
  kind: light
  embed: 64
  layers: 3
completion:
  epochs: 100
  batch: 512
  lr: 1.0e-3
  weight_decay: 1.0e-5
  usage: 1.0
  balance: 1.0
  grad_clip: 1.0
  val: 0.1
  patience: 10
recommendation:
  epochs: 100
  batch: 1024
  lr: 1.0e-3
  weight_decay: 1.0e-5
  negatives: 1
  grad_clip: 1.0
  val: 0.1
  patience: 10
eval:
  ks: [10, 20]
  robustness: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
  ablations: [no_retrieval, no_pe, no_codebook]
serve:
  host: 0.0.0.0
  port: 8080
  workers: 1
log:
  level: INFO
  structured: true
  directory: runs
```

Load it:

```python
from morel import Config

config = Config.load("configs/synthetic.yaml")
```

Or from the CLI:

```bash
python -m morel train completion --config configs/synthetic.yaml
```

### Programmatically

```python
from morel import Config

config = Config.defaults()
config = Config.from_dict({...})         # from a nested dict
config = Config.from_yaml("path.yaml")  # convenience, same as Config.load
```

`Config.defaults()` returns a fully populated `Config` with every
field at its shipped default. Field-level overrides work too:

```python
from dataclasses import replace
from morel import Config

config = Config.defaults()
config = Config(masking=replace(config.masking, ratio=0.6))
```

Because `Config.__post_init__` calls `validate()`, a ratio outside
`[0, 1]` raises `Cfg` at construction time, not somewhere downstream.

## Override at runtime

### From environment variables

```python
config = Config.env()
```

Recognised variables: `MOREL_SEED`, `MOREL_DEVICE`. For more than
two overrides, use a YAML file.

### On the CLI

Every subcommand accepts `--config` and an optional
`--epochs` / `--items` / `--users` override that swaps the matching
field without rewriting the config on disk. The recorded run
manifest always reflects the **resolved** config, not the override.

## Save a config

```python
config.save("configs/my.yaml")
```

The YAML round-trips bit-exactly through `Config.load`, so a
downstream `Config.hash()` is stable across the save / load cycle and
the manifest's `cfg_hash` field binds a run to its config.

## Field reference

See [Reference: config](../reference/config.md) for the full table of
fields with a one-line description of each.
