"""Tests for morel.data.manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from morel.core.errors import Datum
from morel.data.manifest import Manifest, checksum, load, locate, save


class Checker:
    """Aggregated test methods for this module."""

    def save(self, tmp_path: Path) -> None:
        artifact = tmp_path / "x.npz"
        artifact.write_text("hello")
        m = Manifest(
            dataset="Beauty",
            version="1",
            code="abc123",
            seed=0,
            extractor="text",
            cfg_hash="deadbeef",
        )
        sidecar = save(artifact, m)
        assert sidecar.exists()
        loaded = load(artifact)
        assert loaded.dataset == "Beauty"
        assert loaded.seed == 0
        assert loaded.schema == 1

    def load(self, tmp_path: Path) -> None:
        artifact = tmp_path / "x.npz"
        artifact.write_text("hello")
        m = Manifest(
            dataset="Beauty",
            version="1",
            code="abc",
            seed=0,
            extractor="text",
            cfg_hash="hash1",
        )
        save(artifact, m)
        with pytest.raises(Datum):
            load(artifact, expected_config_hash="hash2")

    def missing(self, tmp_path: Path) -> None:
        with pytest.raises(Datum):
            load(tmp_path / "missing.npz")

    def checksum(self, tmp_path: Path) -> None:
        p = tmp_path / "x"
        p.write_text("hello world")
        assert checksum(p) == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def path(self, tmp_path: Path) -> None:
        p = tmp_path / "data.npz"
        assert locate(p).name == "data.npz.manifest.json"

    def malformed(self) -> None:
        with pytest.raises(Datum, match="valid JSON"):
            Manifest.parse_json("not-json")
        with pytest.raises(Datum, match="missing fields"):
            Manifest.parse_json("{}")
        with pytest.raises(Datum, match="valid JSON"):
            Manifest.parse_json("[" * 2_000 + "]" * 2_000)

    def bounded(self, tmp_path: Path) -> None:
        """Manifest sidecars are bounded before parsing."""
        from morel.data.manifest import MAX_MANIFEST_BYTES

        artifact = tmp_path / "x.npz"
        artifact.write_text("data")
        sidecar = locate(artifact)
        sidecar.write_text("x" * (MAX_MANIFEST_BYTES + 1), encoding="utf-8")
        with pytest.raises(Datum, match="exceeds"):
            load(artifact)

    def invalid_types(self) -> None:
        payload = {
            "dataset": "Beauty",
            "version": "1",
            "code": "abc",
            "seed": True,
            "extractor": "text",
            "cfg_hash": "hash",
            "parents": [],
            "schema": 1,
            "timestamp": "2026-01-01T00:00:00+00:00",
            "extras": {},
        }
        with pytest.raises(Datum, match="seed"):
            Manifest.parse_json(json.dumps(payload))
