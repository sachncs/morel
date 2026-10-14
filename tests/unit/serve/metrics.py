"""Tests for Prometheus metric boundary validation."""

from __future__ import annotations

import math

import pytest

from morel.serve.metrics import Registry


class Checker:
    """Aggregated tests for the serving metrics registry."""

    def rejects_invalid_values(self) -> None:
        """NaN, infinity, and negative counters never enter exposition state."""
        registry = Registry()
        with pytest.raises(ValueError, match="non-negative finite"):
            registry.counter_inc("requests", {}, math.nan)
        with pytest.raises(ValueError, match="non-negative finite"):
            registry.histogram_observe("latency", {}, -1.0)
        with pytest.raises(ValueError, match="finite"):
            registry.gauge_set("temperature", {}, math.inf)
        with pytest.raises(ValueError, match="non-negative finite"):
            registry.observe_request(endpoint="/health", method="GET", status=200, elapsed=-1.0)

    def renders_valid_values(self) -> None:
        """Valid metric samples remain standard Prometheus exposition."""
        registry = Registry()
        registry.counter_inc("requests", {"kind": "test"})
        registry.gauge_set("temperature", {}, -2.0)
        registry.histogram_observe("latency", {}, 0.01)
        output = registry.render()
        assert 'requests{kind="test"} 1.0' in output
        assert "temperature -2.0" in output
        assert "latency_count 1.0" in output
