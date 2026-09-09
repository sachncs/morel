# How to add a custom component

morel's stages — retrieval, encoding, routing, codebook, completion,
and recommendation — are registered as factories and selected by a
`kind` field in the config. Adding a new implementation does not
require touching morel.

## The pattern

Every stage exposes a registry and a `build(kind, ...)` function that
returns a constructed module. Pick the registry that matches your
stage:

| Stage       | Registry module                | ``Config`` field    |
|-------------|--------------------------------|---------------------|
| Retrieval   | ``morel.retrieve.STRATEGIES``  | ``retrieve.kind``   |
| Encoding    | ``morel.encode.ENCODERS``      | ``encode.kind``     |
| Routing     | ``morel.route.ROUTERS``        | ``route.kind``      |
| Codebook    | ``morel.codebook.CODEBOOKS``   | ``codebook.kind``   |
| Completion  | ``morel.complete.COMPLETERS``  | ``complete.kind``   |
| Recommendation | ``morel.recommend.RECOMMENDERS`` | ``recommend.kind`` |
| Masking     | ``morel.data.MASKS``           | ``masking.kind``    |
| Extraction  | ``morel.data.EXTRACTORS``      | ``encoder.text`` / ``encoder.visual`` |

Use `register(name)` to add a new factory:

```python
from morel.codebook import CODEBOOKS


@CODEBOOKS.register("my-codebook")
def build_my_codebook(*, dim, size, router, seed=None):
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

from morel.codebook import CODEBOOKS


class SparseCodebook(nn.Module):
    """A codebook that keeps the top-K most-used entries live at any time.

    Each forward call records which entries were used and zeros out
    the gradient on entries that have not been touched in the last
    ``decay`` steps. The exposed ``.usage`` and ``.balance`` losses
    mirror the shipped Soft codebook so a config swap is a no-op for
    the rest of the pipeline.
    """

    def __init__(self, *, dim: int, size: int, router: nn.Module,
                 seed: int | None = None) -> None:
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


@CODEBOOKS.register("sparse")
def build(*, dim, size, router, seed=None):
    return SparseCodebook(dim=dim, size=size, router=router, seed=seed)
```

Put this in your own project, import it once at startup, and select
it from config:

```yaml
codebook:
  kind: sparse
  size: 256
```

## Notes on contracts

- Every factory takes its keyword arguments by name and may ignore
  some; this keeps the signature compatible with the shipped
  factories and lets a config cross-compile.
- A registered name conflicts with an existing factory unless
  ``replace=True`` is passed to ``register``.
- Custom factories in test code are fine; pytest discovers them
  once the test module is imported.

## See also

- [Architecture: extension points](../concepts/architecture.md#extension-points)
  — the full table of registries.
- [Reference: API](../reference/api.md) — auto-generated from every
  module's `__all__`.
