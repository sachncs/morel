"""Check that published examples and repository links stay current."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    ROOT / "README.md",
    ROOT / "SECURITY.md",
    *sorted((ROOT / "docs").rglob("*.md")),
)
SITE_CONTENT = ROOT / "site" / "src" / "lib" / "content.ts"
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def local_readme_links() -> list[str]:
    """Return broken repository-relative links found in the README."""
    broken: list[str] = []
    readme = ROOT / "README.md"
    for target in MARKDOWN_LINK.findall(readme.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#", 1)[0]
        if path and not (ROOT / path).exists():
            broken.append(target)
    return broken


def main() -> int:
    """Fail when tracked examples contain removed API names or false claims."""
    text = "\n".join(path.read_text(encoding="utf-8") for path in (*DOCS, SITE_CONTENT))
    forbidden = {
        "item_cooccurrence": "use morel.data.build.cooccurrence",
        "attach_corpus": "use Pipeline.attach",
        "Pydantic v2": "the configuration is built from frozen dataclasses",
    }
    stale = [f"{name} ({replacement})" for name, replacement in forbidden.items() if name in text]
    if stale:
        raise SystemExit("stale documentation API/claim(s): " + ", ".join(stale))
    broken = local_readme_links()
    if broken:
        raise SystemExit("broken local README link(s): " + ", ".join(broken))
    print(f"documentation API check passed: {len(DOCS)} Markdown files and site content")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
