"""Generate the docs/API.md reference from each module's ``__all__``.

The previous docs/API.md was hand-maintained and listed roughly 30%
non-existent names (e.g. MorelError, Encoder, recall_at_k). This
script walks every package in :mod:`morel`, reads each ``__init__.py``'s
``__all__``, and emits a Markdown reference that cannot drift from the
code. Wire it into ``morel render-api`` and into the CI docs workflow.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from types import ModuleType


def _public(module: ModuleType) -> list[str]:
    """Return the module's ``__all__`` as a sorted, de-duplicated list."""
    entries = list(getattr(module, "__all__", []) or [])
    seen: set[str] = set()
    ordered: list[str] = []
    for entry in entries:
        if entry in seen:
            continue
        seen.add(entry)
        ordered.append(entry)
    return sorted(ordered)


def _doc_first_line(module: ModuleType, name: str) -> str:
    """Return the docstring's first non-empty line for ``name``, or ''."""
    obj = getattr(module, name, None)
    doc = getattr(obj, "__doc__", None) if obj is not None else None
    if not doc:
        return ""
    for line in doc.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return str(stripped)
    return ""


def generate(top: str = "morel") -> str:
    """Walk ``top`` and emit the API reference Markdown.

    Args:
        top: Top-level package name. Modules under it are imported in
            order and their ``__all__`` is rendered.

    Returns
    -------
        The Markdown body to write to disk.
    """
    pkg = importlib.import_module(top)
    if not hasattr(pkg, "__path__"):
        raise RuntimeError(f"{top} is not a package")

    lines = [
        "# morel — API",
        "",
        "The morel API is the union of each package's `__all__`. This page is",
        "machine-generated from the actual `__all__` of every module so it cannot",
        "drift. Regenerate with `morel render-api` (or `python -m",
        "morel.devtools.gen_api`).",
        "",
    ]

    # The top-level package itself: list its own re-exports as the
    # canonical entry point, then show every subpackage heading with its
    # own symbols.
    top_entries = _public(pkg)
    if top_entries:
        lines.append(f"## {top}")
        lines.append("")
        lines.append("```python")
        lines.append(f"from {top} import (")
        for entry in top_entries:
            lines.append(f"    {entry!r},")
        lines.append(")")
        lines.append("```")
        lines.append("")
        for entry in top_entries:
            doc = _doc_first_line(pkg, entry)
            if doc:
                lines.append(f"- `{entry}` — {doc}")
            else:
                lines.append(f"- `{entry}`")
        lines.append("")

    for sub_name in sorted(pkg.__path__):
        sub_path = Path(sub_name)
        if not sub_path.is_dir():
            continue
        for child in sorted(sub_path.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("_") and child.name != "__pycache__":
                continue
            if child.name == "__pycache__":
                continue
            full_name = f"{top}.{child.name}"
            if child.name == top.split(".")[-1]:
                # The package directory has the same name as the top
                # package itself (e.g. morel/morel/__init__.py); skip
                # it to avoid double-rendering as morel.morel.
                continue
            try:
                sub = importlib.import_module(full_name)
            except Exception as exc:
                lines.append(f"## {full_name}")
                lines.append("")
                lines.append(f"_(import error: {exc})_")
                lines.append("")
                continue
            entries = _public(sub)
            if entries:
                lines.append(f"## {full_name}")
                lines.append("")
                lines.append("```python")
                lines.append(f"from {full_name} import (")
                for entry in entries:
                    lines.append(f"    {entry!r},")
                lines.append(")")
                lines.append("```")
                lines.append("")
                for entry in entries:
                    doc = _doc_first_line(sub, entry)
                    if doc:
                        lines.append(f"- `{entry}` — {doc}")
                    else:
                        lines.append(f"- `{entry}`")
                lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(prog="morel render-api")
    parser.add_argument("output", nargs="?", default="docs/API.md", help="output Markdown path")
    parser.add_argument("--top", default="morel", help="top-level package")
    args = parser.parse_args(argv)
    body = generate(args.top)
    Path(args.output).write_text(body, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


__all__ = ["generate", "main"]
