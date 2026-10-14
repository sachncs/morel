"""Tests for morel.data.acquire."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from morel.core.errors import Datum
from morel.data.acquire import fetch


class Checker:
    """Aggregated test methods for this module."""

    def fetch(self, tmp_path: Path) -> None:
        target = tmp_path / "x.bin"
        with patch("morel.data.acquire.urllib.request.urlopen") as mocked:
            mocked.return_value.__enter__.return_value.read.side_effect = [b"hello", b""]
            path = fetch("https://example.invalid/x.bin", target, timeout=5, retries=0)
        assert path.exists()
        assert path.read_bytes() == b"hello"

    def retries(self, tmp_path: Path) -> None:
        target = tmp_path / "x.bin"
        with (
            patch("morel.data.acquire.urllib.request.urlopen", side_effect=OSError("boom")),
            pytest.raises(Datum),
        ):
            fetch("https://example.invalid/x.bin", target, timeout=1, retries=2, backoff=1.0)

    def bounded_atomic(self, tmp_path: Path) -> None:
        """Reject oversized transfers without replacing an existing artifact."""
        target = tmp_path / "x.bin"
        target.write_bytes(b"old")
        with patch("morel.data.acquire.urllib.request.urlopen") as mocked:
            response = mocked.return_value.__enter__.return_value
            response.length = 5
            response.read.side_effect = [b"hello", b""]
            with pytest.raises(Datum, match="exceeds"):
                fetch("https://example.invalid/x.bin", target, retries=0, max_bytes=4)
        assert target.read_bytes() == b"old"

        with patch("morel.data.acquire.urllib.request.urlopen") as mocked:
            response = mocked.return_value.__enter__.return_value
            response.length = None
            response.read.side_effect = [b"new", OSError("connection dropped")]
            with pytest.raises(Datum, match="failed to fetch"):
                fetch("https://example.invalid/x.bin", target, retries=0)
        assert target.read_bytes() == b"old"
