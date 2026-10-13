# How to add a custom component

morel's stages — retrieval, encoding, routing, codebook, completion,
and recommendation — are selected by a `kind` field in the config. Built-in
construction is routed through typed adapters and runtime contracts; production
registries are intentionally not mutable at runtime.

## The pattern

Every stage exposes a public `KIND` mapping for introspection and a
`build(kind, ...)` function. Pick the package that matches your stage:

| Stage       | Registry module                | ``Config`` field    |
|-------------|--------------------------------|---------------------|
| Retrieval   | ``morel.retrieve.KIND``        | ``retrieve.kind``   |
| Encoding    | ``morel.encode.KIND``           | ``encode.kind``     |
| Routing     | ``morel.route.KIND``            | ``route.kind``      |
| Codebook    | ``morel.codebook.KIND``         | ``codebook.kind``   |
| Completion  | ``morel.complete.KIND``         | ``complete.kind``   |
| Recommendation | ``morel.recommend.KIND``     | ``recommend.kind`` |
| Masking     | ``morel.data.MASKS``            | ``masking.kind``    |
| Extraction  | ``morel.data.EXTRACTORS``      | ``encoder.text`` / ``encoder.visual`` |

To add a new implementation, add a typed adapter to the owning package and
validate its protocol before exposing the new configuration name:

```python
from morel.codebook import Codebook


def build_my_codebook(*, dim: int, size: int, router, seed=None) -> Codebook:
    return MyCodebook(dim=dim, size=size, router=router, seed=seed)
```

Then select it from YAML:

```yaml
codebook:
  kind: my-codebook
  size: 256
```

## A worked example: a custom codebook

```python
import torch
import torch.nn as nn


class SparseCodebook(nn.Module):
    """A codebook that keeps the top-K most-used entries live at any time.

    Each forward call records which entries were used and zeros out
    the gradient on entries that have not been touched in the last
    ``decay`` steps. The exposed ``.usage`` and ``.balance`` losses
    mirror the shipped Soft codebook so a config swap is a no-op for
    the rest of the pipeline.
    """

    def __init__(self, *, dim: int, size: int, router: nn.Module, seed: int | None = None) -> None:
        super().__init__()
        self.dim = dim
        self.size = size
        self.router = router
        self.codebook = nn.Embedding(size, dim)
        self.decay = 0.99

    def forward(self, z):
        g = self.router(z)
        weights = g @ self.codebook.weight
        return weights, g


def build(*, dim: int, size: int, router, seed=None) -> Codebook:
    return SparseCodebook(dim=dim, size=size, router=router, seed=seed)
```

Put the adapter in a fork or an explicitly maintained integration package,
include it in that package's typed factory map, and select it from config:

```yaml
codebook:
  kind: sparse
  size: 256
```

## Notes on contracts

- Every adapter takes its keyword arguments by name and may ignore
  some; this keeps the signature compatible with the shipped
  factories and lets a config cross-compile.
- The adapter result must satisfy the stage protocol before it enters
  composition; incompatible values fail with the typed ``Cfg`` error.
- Custom adapters should be covered by contract tests before deployment.

## See also

- [Architecture: extension points](../concepts/architecture.md#extension-points)
  — the full table of registries.
- [Reference: API](../reference/api.md) — auto-generated from every
  module's `__all__`.
