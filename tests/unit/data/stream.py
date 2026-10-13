"""Tests for streaming data ingestion boundaries."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from morel.core.errors import Datum
from morel.data.stream import confirmed, cooc


class Checker:
    """Aggregated tests for malformed and bounded stream inputs."""

    def malformed_records(self, tmp_path: Path) -> None:
        """Non-object, malformed, and incomplete lines are ignored safely."""
        from morel.data.stream import review, stream

        path = tmp_path / "reviews.json"
        path.write_text(
            "\n".join(
                [
                    "[]",
                    "not-json",
                    json.dumps({"reviewerID": "u1"}),
                    json.dumps({"reviewerID": "u1", "asin": "i1"}),
                ]
            ),
            encoding="utf-8",
        )
        chunks = list(review(path, chunk_size=2))
        assert chunks == [[{"reviewerID": "u1"}, {"reviewerID": "u1", "asin": "i1"}]]
        assert list(stream(path, min_edges=1, chunk_size=2))

    def invalid_parameters(self, tmp_path: Path) -> None:
        from morel.data.stream import review, stream

        path = tmp_path / "reviews.json"
        path.write_text("{}\n", encoding="utf-8")
        with pytest.raises(Datum, match="positive integer"):
            list(review(path, chunk_size=0))
        with pytest.raises(Datum, match="positive integer"):
            list(stream(path, min_edges=0))
        with pytest.raises(Datum, match="positive integer"):
            confirmed(path, chunk_size=0)

    def invalid_graph_chunk(self) -> None:
        with pytest.raises(Datum, match="catalog bounds"):
            cooc(iter([(np.array([0]), np.array([4]))]), items=4)
        with pytest.raises(Datum, match="equal lengths"):
            cooc(iter([(np.array([0]), np.array([0, 1]))]), items=4)

    def duplicate_edges_do_not_inflate_kcore(self, tmp_path: Path) -> None:
        """The exact two-pass filter counts unique user-item edges only."""
        path = tmp_path / "duplicates.json"
        path.write_text(
            "\n".join(
                [
                    json.dumps({"reviewerID": "u1", "asin": "i1"}),
                    json.dumps({"reviewerID": "u1", "asin": "i1"}),
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(Datum, match="empty interaction"):
            confirmed(path, min_edges=2)
