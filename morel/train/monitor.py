"""JSONL metrics monitor."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from morel.core.errors import Train

MAX_METRICS_BYTES = 16 << 20


class Monitor:
    """Append ``(time, **metrics)`` lines to ``metrics.jsonl``.

    Attributes:
        directory: Directory where metrics are written.
        path: Full path to the ``metrics.jsonl`` file.
    """

    def __init__(self, directory: Path | str) -> None:
        """Initialize the metrics monitor.

        Args:
            directory: Directory to write ``metrics.jsonl`` to.
        """
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "metrics.jsonl"

    def log(self, step: int | None = None, **metrics: Any) -> None:
        """Append one JSONL line."""
        record: dict[str, Any] = {"time": time.time()}
        if step is not None:
            record["step"] = int(step)
        record.update(metrics)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str, ensure_ascii=False))
            handle.write("\n")

    def latest(self) -> dict[str, Any] | None:
        """Return the most recent record or None if empty."""
        if not self.path.exists():
            return None
        try:
            if self.path.stat().st_size > MAX_METRICS_BYTES:
                raise Train(f"metrics file exceeds the {MAX_METRICS_BYTES}-byte limit: {self.path}")
            last_line: str | None = None
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    last_line = line
        except Train:
            raise
        except (OSError, UnicodeError) as exc:
            raise Train(f"unable to read metrics file: {self.path}") from exc
        if last_line is None:
            return None
        try:
            record = json.loads(last_line)
        except (json.JSONDecodeError, RecursionError) as exc:
            raise Train(f"metrics file has an invalid final record: {self.path}") from exc
        if not isinstance(record, dict):
            raise Train(f"metrics file final record must be an object: {self.path}")
        return record


__all__ = ["MAX_METRICS_BYTES", "Monitor"]
