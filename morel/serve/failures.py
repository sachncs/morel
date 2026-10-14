"""Typed policy for failures crossing the serving boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from morel.core.errors import Error


class FailureKind(Enum):
    """Operational class used to select status and retry semantics."""

    DEPENDENCY = "dependency"
    DOMAIN = "domain"
    PROGRAMMER = "programmer"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class FailurePolicy:
    """Public behavior for one classified serving failure."""

    kind: FailureKind
    status_code: int
    detail: str
    retryable: bool


def classify(exc: BaseException) -> FailurePolicy:
    """Classify a recommender failure without exposing implementation details."""
    if isinstance(exc, TimeoutError):
        return FailurePolicy(
            FailureKind.TIMEOUT,
            504,
            "recommender scoring timed out; retry after the service recovers",
            True,
        )
    if isinstance(exc, Error):
        return FailurePolicy(
            FailureKind.DOMAIN,
            503,
            "recommender scoring is unavailable; see server logs with the request id",
            True,
        )
    if isinstance(exc, (OSError, RuntimeError)):
        return FailurePolicy(
            FailureKind.DEPENDENCY,
            503,
            "recommender scoring is unavailable; see server logs with the request id",
            True,
        )
    return FailurePolicy(
        FailureKind.PROGRAMMER,
        500,
        "unexpected serving failure; see server logs with the request id",
        False,
    )


__all__ = ["FailureKind", "FailurePolicy", "classify"]
