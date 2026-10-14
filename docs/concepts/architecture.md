# Architecture

morel is organised as a small set of replaceable pipeline stages. The public
surface stays simple: build a graph, attach features, run the pipeline, and
rank. The modules underneath it keep data preparation, algorithms, training,
and serving separate.

The interactive map below is rendered by Astro, not stored as a Markdown
flowchart. Hover or focus a stage to see its responsibility.

<!-- architecture-diagram -->

## How the modules fit together

The dependency direction is intentionally one-way:

- `core` owns configuration, seeds, devices, errors, types, and logging.
- `data`, `graph`, `encode`, `retrieve`, `route`, `codebook`, `complete`, and
  `recommend` implement the reusable building blocks.
- `pipeline` composes those blocks into the end-to-end pass.
- `train` and `eval` add experiments and measurement around the model.
- `app` provides experiment, benchmark, and reproduce services.
- `cli` is a thin command dispatcher; `serve` exposes inference over HTTP.

Higher layers may call lower layers. Lower layers never import the application
or command-line layers. The architecture test checks the import graph on every
run so a convenient shortcut cannot quietly create a cycle.

## Package map

| Package | Responsibility |
| --- | --- |
| `morel.core` | Config, seeds, devices, logging, errors, types, paths, fidelity |
| `morel.data` | Acquire, validate, extract, build, mask, and store data |
| `morel.graph` | Bipartite graphs, item graphs, subgraphs, Laplacian features |
| `morel.retrieve` | Anchor, ACS, MAGE, and BFS retrieval strategies |
| `morel.encode` | Feature encoders, pooling, and graph-transformer context encoding |
| `morel.route` | Dense, top-k, Gumbel, and fixed routing |
| `morel.codebook` | Vector quantisation and usage/balance losses |
| `morel.complete` | Per-modality decoders for missing features |
| `morel.recommend` | LightGCN, matrix-factorisation, popularity, and BPR heads |
| `morel.pipeline` | The end-to-end composition boundary |
| `morel.train` / `morel.eval` | Training loops, checkpoints, metrics, and ablations |
| `morel.app` / `morel.cli` | User-facing services and command dispatch |
| `morel.serve` | FastAPI inference with bearer-token auth |

## Extension points

The config selects a stage with a `kind`. Each implementation must register a
typed adapter and satisfy the stage protocol before it can enter the pipeline.
Unknown names fail with a typed configuration error listing the valid options.
Production registries are not mutable at runtime.

| Config field | Example kinds |
| --- | --- |
| `masking.kind` | `bernoulli`, `block` |
| `retrieve.kind` | `mage`, `acs`, `anchor`, `bfs`, `none` |
| `encode.kind` | `transformer`, `identity` |
| `route.kind` | `top`, `dense`, `gumbel`, `fixed` |
| `codebook.kind` | `gumbel`, `vq`, `identity` |
| `recommend.kind` | `light`, `mf`, `pop` |

For a complete list of fields, see the [configuration reference](../reference/config.md).
For a worked extension, see [add a custom component](../howto/custom-component.md).

## Determinism and boundaries

The resolved config, dataset version, seed, extractor, and code hash are
recorded in a manifest. Inference switches the pipeline to evaluation mode;
the ranker and routing decisions are therefore repeatable for the same inputs.
Serving refuses to continue when the real pipeline, graph, corpus, or
recommender is unavailable.
