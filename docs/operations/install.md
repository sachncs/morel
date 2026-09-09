# Operations — install

morel is published as a wheel and source distribution. This page
documents the supported install patterns.

## Python

Tested against CPython 3.10, 3.11, 3.12, and 3.13. Earlier versions
fail at import time because of PEP 604 ``int | None`` annotations
used throughout the public API.

## Dependencies

The runtime dependencies declared in ``pyproject.toml``:

- ``torch>=2.0,<3``
- ``numpy>=1.24,<3``
- ``scipy>=1.10,<2``
- ``sentence-transformers>=2.2,<7``
- ``torchvision>=0.15,<1``
- ``Pillow>=10.0,<13``
- ``pandas>=2.0,<3``
- ``pyyaml>=6.0,<7``
- ``pydantic>=2.0,<3``

### Optional extras

| Extra     | Installs                                            |
|-----------|-----------------------------------------------------|
| ``[serve]``  | FastAPI, uvicorn, prometheus-client, httpx        |
| ``[bench]``  | ``pytest-benchmark``                              |
| ``[text]``   | sentence-transformers (required for text encoders) |
| ``[vision]`` | torchvision (required for visual encoders)        |
| ``[dev]``    | pytest stack, ruff, mypy, mkdocs, pip-audit, build, twine |

## Install patterns

### PyPI

```bash
pip install morel
```

This installs the runtime dependencies plus the package. The
``[serve]``, ``[bench]``, ``[text]``, and ``[vision]`` extras are
**not** pulled in automatically — install the one(s) you need:

```bash
pip install 'morel[serve]'
pip install 'morel[serve,bench]'
```

### From source

```bash
git clone https://github.com/sachncs/morel.git
cd morel
pip install -e '.[dev]'
```

The ``-e`` editable install lets you iterate on the package without
re-installing.

### Docker

```bash
docker build -t morel:latest .
docker compose up --build
```

The shipped ``Dockerfile`` is multi-stage: a build stage that
installs ``.[dev]``, and a runtime stage that only carries the
non-test dependencies and runs as a non-root user.

## Reproducibility

``requirements.lock`` is a hash-pinned lockfile generated from
``pyproject.toml``:

```bash
make lock
```

This is the install flavour CI uses; the lock is checked against
``pyproject.toml`` on every PR via ``make lock-check``.

## Determinism

``morel.core.seed.seed(value)`` configures deterministic seeding for
torch, torch CUDA, numpy, Python ``random``, ``PYTHONHASHSEED``, and
cuDNN:

```python
from morel import seed_everything

seed_everything(42)
```

For a scoped variant (restoring the caller's RNG state on exit):

```python
from morel.core.seed import deterministic

with deterministic(42):
    pipeline = build_pipeline(config)
```

A run that has been seeded this way is bit-identical across
reruns on the same torch version. CUDA non-determinism in
``torch.sparse.mm`` is documented under
[Reference: limitations](../reference/limitations.md).

## Verification

After installing, run the smoke test:

```bash
python -m pytest tests/unit -x
```

The full suite takes a few minutes and asserts the unit, property,
and integration paths. CI runs the same suite on every push.
