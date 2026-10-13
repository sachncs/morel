"""Verify that published local verification metrics match the current run."""

from __future__ import annotations

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collected_tests() -> int:
    """Return the number of tests after the repository's collection filter."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-cov"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"morel verification count: (\d+)", result.stdout + result.stderr)
    if match is None:
        raise RuntimeError("pytest did not report the post-filter test count")
    return int(match.group(1))


def coverage_percent() -> float:
    """Return combined line/branch coverage from the current XML report."""
    report = ROOT / "coverage.xml"
    if not report.exists():
        raise RuntimeError("coverage.xml is missing; run the test suite first")
    root = ET.parse(report).getroot()
    valid = int(root.attrib["lines-valid"]) + int(root.attrib["branches-valid"])
    covered = int(root.attrib["lines-covered"]) + int(root.attrib["branches-covered"])
    if valid <= 0:
        raise RuntimeError("coverage.xml contains no measurable lines or branches")
    return round(100.0 * covered / valid, 2)


def main() -> int:
    """Check every tracked verification surface."""
    tests = collected_tests()
    coverage = coverage_percent()
    coverage_text = f"{coverage:.2f}"
    checks = {
        ROOT / "AUDIT.md": f"**{tests} passed**, {coverage_text}% coverage",
        ROOT
        / "docs/reference/production-readiness.md": f"{tests} passed, {coverage_text}% coverage",
        ROOT / "docs/getting-started.md": f"{tests} tests with {coverage_text} % coverage",
        ROOT / "site/src/lib/content.ts": f"tests: {tests},",
        ROOT / "docs/index.md": f"{tests} tests · {coverage_text}% coverage",
    }
    missing = [
        str(path.relative_to(ROOT))
        for path, text in checks.items()
        if text not in path.read_text(encoding="utf-8")
    ]
    if missing:
        raise SystemExit(
            f"verification metrics are stale: expected {tests} tests / "
            f"{coverage_text}% coverage in {', '.join(missing)}"
        )
    print(f"verification metrics match: {tests} tests / {coverage_text}% coverage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
