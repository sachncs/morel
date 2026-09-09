# Docs hub

The morel documentation is split by audience. The homepage links to
each of these in one click; this hub is the long-form version, with
full reading paths and cross-references.

## Sections at a glance

- **[Getting started](getting-started.md)** — install, demo, smoke
  test, the minimal example.
- **[Installation](operations/install.md)** — pinned lockfile, Docker,
  CUDA, dev extras.
- **[Method](concepts/method.md)** — notation, the seven stages, and
  the per-stage equations.
- **[Architecture](concepts/architecture.md)** — module layering, data
  flow, extension points, the machine-checked layering test.
- **[Experiments](operations/reproduce.md)** — reproducing a run
  end-to-end from its manifest and config.
- **[API reference](reference/api.md)** — every public symbol,
  generated from each module's `__all__`. Updated by
  `morel render-api`.
- **[Tutorials](tutorials/index.md)** — three ordered walk-throughs:
  synthetic data, real Amazon data, serve over HTTP.
- **[Contributing](project/contributing.md)** — dev setup, code style,
  commit messages, release process.
- **[Changelog](project/changelog.md)** — release-by-release
  record of every notable change.

## Reading paths

Pick the path that matches your role; each one is a short ordered list.

### New user

You just want to see morel run.

1. [Getting started](getting-started.md) — five minutes from `pip
   install` to a working end-to-end pass.
2. [Tutorial 1 — synthetic](tutorials/synthetic.md) — what the demo
   does, step by step.
3. [Tutorial 2 — real Amazon data](tutorials/real-data.md) — drop the
   synthetic features and run on a real catalogue.

### Researcher

You want to understand the method, the implementation, and the
fidelity registry before citing the library.

1. [Method](concepts/method.md) — notation, stages, equations.
2. [Architecture](concepts/architecture.md) — module layering and
   data flow.
3. [Reference: paper fidelity](reference/fidelity.md) — which paper
   equations map to which code paths.
4. [Reference: benchmarks](reference/benchmarks.md) and
   [Reference: production readiness](reference/production-readiness.md)
   — the evidence story.

### Contributor

You want to add a stage, swap an implementation, or push a PR.

1. [Architecture](concepts/architecture.md) — the layering rules.
2. [How-to: add a custom component](howto/custom-component.md) —
   register a new factory and select it from config.
3. [How-to: configure morel](howto/configure.md) — every config
   field, with a plain-English description.
4. [Contributing](project/contributing.md) — workflow, commit
   messages, tests.

### Reviewer

You want to audit a claim. The paper-fidelity registry is the
canonical link between paper sections and code.

1. [Reference: paper fidelity](reference/fidelity.md) — every paper
   component bound to its implementation and test.
2. [Operations: reproduce](operations/reproduce.md) — re-run a saved
   experiment deterministically from its manifest.
3. [Reference: production readiness](reference/production-readiness.md)
   — the audit trail across the codebase.

## How the docs are organized

```
Home (index.md)
└── Docs hub (this page)
    ├── Getting started
    ├── Tutorials
    │   ├── Tutorial 1 — synthetic
    │   ├── Tutorial 2 — real Amazon data
    │   └── Tutorial 3 — serve over HTTP
    ├── How-to
    │   ├── Configure morel
    │   ├── Add a custom component
    │   └── Serve in production
    ├── Concepts
    │   ├── Method
    │   └── Architecture
    ├── Reference
    │   ├── API (auto-generated)
    │   ├── CLI
    │   ├── Config
    │   ├── Paper fidelity
    │   ├── Benchmarks
    │   ├── Production readiness
    │   └── Limitations
    ├── Operations
    │   ├── Install
    │   ├── Reproduce
    │   ├── Deploy
    │   ├── Observability
    │   └── GitHub Pages
    └── Project
        ├── Changelog
        ├── Security
        ├── Contributing
        └── License
```

## Conventions used throughout the docs

- **Code blocks** carry a language tag (`python`, `bash`, `yaml`,
  …). Plain prose is the only thing without a tag.
- **Tables** carry parallel information in a fixed column order —
  never rearrange columns between rows of the same table.
- **Admonitions** are used sparingly:
  - !!! tip for things that help you decide.
  - !!! warning for things that break your workflow if ignored.
  - !!! danger for things that are security-critical.
- **"See also" links** at the bottom of every page point at the next
  page in the recommended reading order for each role.

## Writing this documentation

If you spot something missing or wrong, open a GitHub issue or
follow the [Contributing](project/contributing.md) guide and send a
pull request. The `mkdocs build --strict` step enforces internal
links on every build, so a broken link fails CI before merge.
