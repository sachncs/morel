"""Artifact manifest.

Every persisted artifact has a sidecar ``.manifest.json`` carrying enough
metadata to answer: what dataset, what version, what preprocessing, what
feature extractor, what configuration, what random seed, what code version.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from morel.core.errors import Datum

VERSION = 1
MAX_MANIFEST_BYTES = 1 << 20


@dataclass
class Manifest:
    """Manifest sidecar for a data artifact.

    Attributes:
        dataset: Dataset name.
        version: Dataset version.
        code: Code version string.
        seed: Random seed used.
        extractor: Extractor name.
        cfg_hash: Configuration hash.
        parents: Parent manifest paths.
        schema: Schema name.
        timestamp: Creation timestamp.
        extras: Additional metadata.
    """

    dataset: str
    version: str
    code: str
    seed: int
    extractor: str
    cfg_hash: str
    parents: list[str] = field(default_factory=list)
    schema: int = VERSION
    timestamp: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())
    extras: dict[str, Any] = field(default_factory=dict)

    def json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(dataclasses.asdict(self), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def parse_json(cls, text: str) -> Manifest:
        """Deserialize and validate a manifest JSON document.

        Manifests are an input boundary: malformed sidecars must become the
        domain-level :class:`Datum` error rather than leaking ``TypeError`` or
        ``KeyError`` from dataclass construction into callers.
        """
        try:
            payload = json.loads(text)
        except (TypeError, json.JSONDecodeError, RecursionError) as exc:
            raise Datum("manifest is not valid JSON") from exc
        if not isinstance(payload, Mapping):
            raise Datum("manifest must contain a JSON object")

        required = {
            "dataset",
            "version",
            "code",
            "seed",
            "extractor",
            "cfg_hash",
            "parents",
            "schema",
            "timestamp",
            "extras",
        }
        missing = sorted(required - payload.keys())
        unknown = sorted(payload.keys() - required)
        if missing:
            raise Datum(f"manifest is missing fields: {', '.join(missing)}")
        if unknown:
            raise Datum(f"manifest contains unknown fields: {', '.join(unknown)}")

        string_fields = ("dataset", "version", "code", "extractor", "cfg_hash", "timestamp")
        if any(
            not isinstance(payload[field], str) or not payload[field] for field in string_fields
        ):
            raise Datum("manifest string fields must be non-empty strings")
        seed = payload["seed"]
        schema = payload["schema"]
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise Datum("manifest seed must be an integer")
        if isinstance(schema, bool) or not isinstance(schema, int) or schema != VERSION:
            raise Datum(f"unsupported manifest schema: {schema!r}")
        parents = payload["parents"]
        if not isinstance(parents, list) or any(not isinstance(parent, str) for parent in parents):
            raise Datum("manifest parents must be a list of strings")
        extras = payload["extras"]
        if not isinstance(extras, dict):
            raise Datum("manifest extras must be an object")
        return cls(
            dataset=payload["dataset"],
            version=payload["version"],
            code=payload["code"],
            seed=seed,
            extractor=payload["extractor"],
            cfg_hash=payload["cfg_hash"],
            parents=parents,
            schema=schema,
            timestamp=payload["timestamp"],
            extras=extras,
        )


def locate(artifact: Path | str) -> Path:
    """Return the sidecar manifest path for an artifact."""
    target = Path(artifact)
    return target.with_suffix(target.suffix + ".manifest.json")


def save(artifact: Path | str, manifest: Manifest) -> Path:
    """Atomically save a manifest next to an artifact.

    Args:
        artifact: Path to the artifact the manifest describes.
        manifest: Manifest payload.

    Returns:
        The manifest path that was written.
    """
    target = Path(artifact).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    sidecar = locate(target)
    tmp = sidecar.with_suffix(sidecar.suffix + ".tmp")
    tmp.write_text(manifest.json(), encoding="utf-8")
    os.replace(tmp, sidecar)
    return sidecar


def load(artifact: Path | str, *, expected_config_hash: str | None = None) -> Manifest:
    """Load a manifest sidecar.

    Args:
        artifact: Path to the artifact whose manifest to load.
        expected_config_hash: If provided, raise Datum on mismatch.

    Returns:
        The loaded Manifest.

    Raises:
        Datum: If the sidecar is missing or its config hash mismatches.
    """
    sidecar = locate(artifact)
    if not sidecar.exists():
        raise Datum(f"manifest not found for {artifact}: {sidecar}")
    try:
        size = sidecar.stat().st_size
        if size > MAX_MANIFEST_BYTES:
            raise Datum(f"manifest exceeds the {MAX_MANIFEST_BYTES}-byte limit: {sidecar}")
        text = sidecar.read_text(encoding="utf-8")
        manifest = Manifest.parse_json(text)
    except Datum:
        raise
    except (OSError, UnicodeError) as exc:
        raise Datum(f"unable to read manifest for {artifact}: {sidecar}") from exc
    if expected_config_hash is not None and manifest.cfg_hash != expected_config_hash:
        raise Datum(
            f"manifest config hash mismatch for {artifact}: "
            f"got {manifest.cfg_hash}, expected {expected_config_hash}"
        )
    return manifest


def checksum(path: Path | str) -> str:
    """Compute SHA256 of a file's contents."""
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


__all__ = [
    "MAX_MANIFEST_BYTES",
    "VERSION",
    "Manifest",
    "checksum",
    "load",
    "locate",
    "save",
]
