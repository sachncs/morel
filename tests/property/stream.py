"""Property checks for streaming ingestion boundaries."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import given, settings
from hypothesis import strategies as st

from morel.core.errors import Datum


class Checker:
    """Aggregated property tests for streamed JSON input."""

    @given(st.binary(max_size=4096))
    @settings(max_examples=100, deadline=None)
    def arbitrary_review_bytes_never_leak_internal_errors(self, payload: bytes) -> None:
        """Arbitrary review bytes reject as ``Datum`` or yield valid records."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "reviews.json"
            path.write_bytes(payload)
            try:
                from morel.data.stream import review

                chunks = list(review(path, chunk_size=8))
            except Datum:
                return
            assert all(len(chunk) <= 8 for chunk in chunks)
            assert all(isinstance(record, dict) for chunk in chunks for record in chunk)
