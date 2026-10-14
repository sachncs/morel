# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Recommender implementations now declare typed capabilities, with registry and
  pipeline validation rejecting mismatches before serving.
- Site visual contracts now use strict 2% pixel-diff thresholds with refreshed
  Linux and macOS baselines, preventing palette regressions from passing as
  acceptable visual drift.
- Hosted site visual checks use a documented cross-renderer raster tolerance
  while the semantic teal-brand contract remains strict.
- Social preview artwork now uses the teal graph/tetrahedral brand mark used by
  the deployed product site.
- Rebrand: `rmr` → `morel` (MOdality-REcommended Links).
- Single-word domain naming applied throughout; implementation visibility now
  follows the public/`_semi_private` convention in `docs/engineering.md`.
- Module structure reorganized around explicit domain boundaries (core → data → model → train → eval → app → cli).
- Strict layering enforced by `tests/unit/test_architecture.py` (stdlib `ast` import-graph check).
- Strict mypy mode for `morel/`.

### Added
- Sparse graph invariant property coverage for arbitrary values, empty and
  degenerate graphs, self-loops, non-finite data, and invalid controls.
- `morel.core` runtime primitives: `Config`, `seed`, `Device`, `Log`, `Fidelity` registry.
- `morel.data` lifecycle: `acquire`, `validate`, `extract`, `build`, `mask`, `store`, `Manifest`.
- `morel.graph` polymorphism: `Graph`, `Bipartite`, `Item`, `Subgraph`, `Laplace`.
- `morel.retrieve` correctness fixes: iterative ACS, best-improvement MAGE, sorted boundary.
- `morel.encode`, `morel.route`, `morel.codebook`, `morel.complete`, `morel.recommend`.
- `morel.pipeline` end-to-end orchestration.
- `morel.train`, `morel.eval`, `morel.app`, `morel.cli`, `morel.serve`.

### Removed
- `.pre-commit-config.yaml` (checks now enforced in CI).
- `rmr/` package (legacy stub remains for one release cycle).

## [0.3.0] - 2026-05-18

### Added
- Initial GRE-MC reproduction baseline (under `rmr`).
- Item-graph construction, missing-modality masking, Laplacian PE.
- Graph transformer, sparse-routing codebook, modality decoders.
- LightGCN downstream recommender.
- Training and evaluation scripts.
- Test suite.

[Unreleased]: https://github.com/sachncs/morel/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/sachncs/morel/releases/tag/v0.3.0
