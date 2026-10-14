# Contributing

Thank you for your interest in `morel`.

## Setup

```bash
git clone https://github.com/sachncs/morel.git
cd morel
python -m pip install -e ".[dev]"
```

## Workflow

1. Create a branch from `master`.
2. Make focused changes.
3. Run the local checks:

   ```bash
   make lint
   make format
   make typecheck
   make test
   ```

   All four must pass before opening a PR.

4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Open a pull request against `master`.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): add new algorithm
fix(scope): correct behaviour
chore(deps): bump numpy
docs: clarify API
test: add coverage for retrieval determinism
refactor: rename _backtrack to backtrack
```

## Code style

- Single-word naming: no `_` prefixes, no suffixes, no `get_`/`compute_`/`make_` prefixes.
- Strict mypy: every public function has typed parameters and return type.
- Test coverage: every new module gets a `tests/unit/<package>/test_<module>.py`.
- No print statements in library code — use the `morel.core.log` logger.

## Architecture

The reference layering is:

```
cli    → app
app    → train | eval
train  → model | data | core
eval   → model | data | core
model  → data | core
data   → core
core   → (nothing in morel)
```

Adding a new algorithm:

1. Define a `Protocol` in the appropriate subpackage.
2. Implement the algorithm.
3. Add a typed adapter to the owning package's private factory registry and
   expose only the package's `KIND` mapping for introspection. For ablations,
   add the transform to `morel.eval.ablation.KIND`.
4. Add unit, property, and research validation tests.

## Release process

1. Add a matching `## [MAJOR.MINOR.PATCH]` section to
   `docs/project/changelog.md`.
2. Push an annotated `vMAJOR.MINOR.PATCH` tag. `setuptools_scm` derives the
   package version from that tag.
3. The release workflow builds one wheel, verifies its metadata against the
   tag and changelog, checks the package metadata, generates an SBOM, and then
   publishes to PyPI via OIDC trusted publishing.

The workflow is tag-only so a branch or manually dispatched job cannot publish
an unversioned development build.

## Contact

- General questions: GitHub Discussions.
- Security: see `SECURITY.md`.
