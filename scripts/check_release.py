"""Validate a versioned release artifact before publication."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG_PATTERN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def metadata_version(wheel: Path) -> str:
    """Read the distribution version from a wheel's core metadata."""
    with zipfile.ZipFile(wheel) as archive:
        metadata_files = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_files) != 1:
            raise RuntimeError(f"expected one METADATA file in {wheel.name}")
        for line in archive.read(metadata_files[0]).decode("utf-8").splitlines():
            if line.startswith("Version: "):
                return line.removeprefix("Version: ").strip()
    raise RuntimeError(f"wheel {wheel.name} has no Version metadata")


def main(argv: list[str] | None = None) -> int:
    """Check the tag, built wheel, and changelog agree on one release version."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or TAG_PATTERN.fullmatch(args[0]) is None:
        raise SystemExit("usage: check_release.py vMAJOR.MINOR.PATCH[-prerelease]")

    tag = args[0]
    version = tag[1:]
    wheels = sorted((ROOT / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one release wheel, found {len(wheels)}")
    built_version = metadata_version(wheels[0])
    if built_version != version:
        raise SystemExit(f"wheel version {built_version!r} does not match tag {tag!r}")

    changelog = (ROOT / "docs/project/changelog.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        raise SystemExit(f"docs/project/changelog.md has no release section for {version}")
    print(f"release metadata verified: {tag} -> {wheels[0].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
