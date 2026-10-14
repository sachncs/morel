"""Tests for the serving failure classification contract."""

from __future__ import annotations

import asyncio

from morel.core.errors import Model
from morel.serve.failures import FailureKind, classify


class Checker:
    """Aggregated tests for stable serving failure policy."""

    def classification_matrix(self) -> None:
        """Map expected failure classes to status, retry, and public kind."""
        cases = (
            (TimeoutError("deadline"), FailureKind.TIMEOUT, 504, True),
            (Model("invalid pipeline"), FailureKind.DOMAIN, 503, True),
            (OSError("backend unavailable"), FailureKind.DEPENDENCY, 503, True),
            (RuntimeError("dependency crashed"), FailureKind.DEPENDENCY, 503, True),
            (ValueError("programmer defect"), FailureKind.PROGRAMMER, 500, False),
        )
        for exception, kind, status_code, retryable in cases:
            policy = classify(exception)
            assert policy.kind is kind
            assert policy.status_code == status_code
            assert policy.retryable is retryable
            assert "backend" not in policy.detail
            assert "programmer" not in policy.detail

        # Cancellation is deliberately not converted into a retryable policy.
        cancellation = classify(asyncio.CancelledError())
        assert cancellation.kind is FailureKind.PROGRAMMER
        assert cancellation.retryable is False
