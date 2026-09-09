"""Prometheus exposition for the /metrics endpoint.

The serve stack exposes ``/metrics`` in the standard Prometheus text
exposition format, so off-the-shelf scrapers parse the response
without any extra adapter. A small lock-protected registry owns the
counter, histogram, and gauge state; the renderer walks it once per
scrape. ``prometheus_client`` is not a dependency — the in-house
implementation is enough to drive any standard Prometheus server.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import Response


# Default histogram bucket boundaries, in seconds. The values follow
# the Prometheus client_python default so dashboards that assume those
# boundaries still work.
DEFAULT_BUCKETS: tuple[float, ...] = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
)


class _HistogramStats:
    """Live histogram state for one label set.

    Attributes
    ----------
        buckets: Cumulative count per bucket. The ``i``-th bucket
            counter is incremented for every observation ``<=``
            ``DEFAULT_BUCKETS[i]`` (when defaults are used).
        total: Cumulative observed value.
        count: Cumulative observation count.
    """

    __slots__ = ("buckets", "count", "total")

    def __init__(self, buckets: list[float]) -> None:
        self.buckets = list(buckets)
        self.total = 0.0
        self.count = 0.0

    def observe(self, value: float, boundaries: tuple[float, ...]) -> None:
        """Record one sample against ``boundaries``."""
        for idx, boundary in enumerate(boundaries):
            if value <= boundary:
                self.buckets[idx] += 1.0
        self.total += value
        self.count += 1.0


@dataclass
class Registry:
    """Lock-protected in-process metrics registry.

    The three metric kinds are tracked in separate ``dict``-of-``dict``
    structures keyed by metric name and label tuples, which keeps the
    renderer logic straightforward and avoids creating dynamic classes
    for every metric.
    """

    counters: dict[str, dict[tuple[tuple[str, str], ...], float]] = field(default_factory=dict)
    histograms: dict[
        str, dict[tuple[tuple[str, str], ...], _HistogramStats]
    ] = field(default_factory=dict)
    gauges: dict[str, dict[tuple[tuple[str, str], ...], float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def counter_inc(self, name: str, labels: dict[str, str], value: float = 1.0) -> None:
        """Increment a counter under ``name`` and ``labels``."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            bucket = self.counters.setdefault(name, {})
            bucket[key] = bucket.get(key, 0.0) + value

    def gauge_set(self, name: str, labels: dict[str, str], value: float) -> None:
        """Set a gauge to ``value`` under ``name`` and ``labels``."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            bucket = self.gauges.setdefault(name, {})
            bucket[key] = value

    def histogram_observe(
        self,
        name: str,
        labels: dict[str, str],
        value: float,
        *,
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ) -> None:
        """Observe one sample against the named histogram."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            bucket = self.histograms.setdefault(name, {})
            stats = bucket.get(key)
            if stats is None:
                stats = _HistogramStats([0.0] * len(buckets))
                bucket[key] = stats
            stats.observe(value, buckets)

    def observe_request(
        self,
        *,
        endpoint: str,
        method: str,
        status: int,
        elapsed: float = 0.0,
    ) -> None:
        """Record one HTTP request, with an optional latency sample."""
        labels = {"endpoint": endpoint, "method": method, "status": str(int(status))}
        self.counter_inc("morel_requests_total", labels)
        if elapsed > 0:
            self.histogram_observe("morel_request_duration_seconds", labels, elapsed)

    def set_updater_gauge(self, name: str, value: float, **labels: str) -> None:
        """Set an updater-state gauge by name."""
        merged = dict(labels)
        self.gauge_set(f"morel_updater_{name}", merged, value)

    def render(self) -> str:
        """Render the registry as Prometheus text format."""
        lines: list[str] = []
        with self._lock:
            for name in sorted(self.counters):
                lines.append(f"# TYPE {name} counter")
                for label_key, value in sorted(self.counters[name].items()):
                    lines.append(_format_line(name, label_key, value))
            for name in sorted(self.histograms):
                lines.append(f"# TYPE {name} histogram")
                for label_key, stats in sorted(self.histograms[name].items()):
                    for idx, bucket_count in enumerate(stats.buckets):
                        bucket_labels = dict(label_key)
                        bucket_labels["le"] = str(DEFAULT_BUCKETS[idx])
                        lines.append(
                            _format_line(
                                f"{name}_bucket",
                                tuple(sorted(bucket_labels.items())),
                                bucket_count,
                            )
                        )
                    lines.append(
                        _format_line(
                            f"{name}_bucket",
                            tuple(
                                sorted({**dict(label_key), "le": "+Inf"}.items())
                            ),
                            stats.count,
                        )
                    )
                    lines.append(_format_line(f"{name}_sum", label_key, stats.total))
                    lines.append(_format_line(f"{name}_count", label_key, stats.count))
            for name in sorted(self.gauges):
                lines.append(f"# TYPE {name} gauge")
                for label_key, value in sorted(self.gauges[name].items()):
                    lines.append(_format_line(name, label_key, value))
        return "\n".join(lines) + "\n"


def _format_line(name: str, label_key: tuple[tuple[str, str], ...], value: float) -> str:
    """Format one metric line in Prometheus text exposition."""
    if not label_key:
        return f"{name} {value}"
    parts = [f'{k}="{_escape(v)}"' for k, v in label_key]
    return f"{name}{{{','.join(parts)}}} {value}"


def _escape(value: str) -> str:
    """Escape label values per the Prometheus exposition spec."""
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


REGISTRY = Registry()


def metrics_response(registry: Registry) -> Response:
    """Build a FastAPI ``Response`` carrying the Prometheus exposition body."""
    from fastapi.responses import Response

    return Response(content=registry.render(), media_type="text/plain; version=0.0.4")


__all__ = [
    "DEFAULT_BUCKETS",
    "REGISTRY",
    "Registry",
    "_HistogramStats",
    "metrics_response",
]


# Any is imported above for tools that want to introspect the registry
# dynamically; static consumers see the dataclass-only API.
_ = Any  # silence the linter about an unused TYPE_CHECKING-time import
