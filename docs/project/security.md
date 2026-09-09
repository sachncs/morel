# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities to **sachncs@gmail.com**.

Do **not** open a public GitHub issue for security-related problems.

## Disclosure Process

1. Email a description of the vulnerability and reproduction steps to **sachncs@gmail.com**.
2. The maintainers will acknowledge receipt within 72 hours.
3. A patch will be developed privately and a coordinated disclosure timeline agreed upon.
4. A CVE will be requested if appropriate.

## Supported Versions

morel is on a 0.x development track. Report vulnerabilities against the
version you ran; the maintainers backport fixes on a best-effort basis
to the most recent commit on `master` and to the latest git tag.

| Source                | Supported | Notes                                                       |
|-----------------------|-----------|-------------------------------------------------------------|
| `master` (latest)     | ✅ Active  | The current development tip on `github.com/sachncs/morel`.  |
| Latest PyPI release   | ✅ Active  | `pip install morel` — the version on the most recent tag.   |
| Older releases        | ❌ No      | The 0.x line moves quickly; please upgrade.                 |

The shipped version is reported by `morel/version.py` and printed by
`morel --version`. Always include that string when filing a report.

## Scope

The package:

- Loads remote datasets via HTTPS with optional SHA256 verification.
- Loads Sentence-Transformers and ResNet-50 weights from public model hubs.
- Does **not** load arbitrary pickle files or remote code.

When loading artifacts:

- Checkpoint files use `torch.load(..., weights_only=True)` (default).
- `np.load` is called with `allow_pickle=False`.
- Remote downloads validate SHA256 where manifests are present.

## Out of scope

- Vulnerabilities in upstream libraries (PyTorch, NumPy, Sentence-Transformers, etc.) should be reported upstream.
