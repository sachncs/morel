"""Bearer-token authentication with separate read and admin scopes.

The serve stack distinguishes:

- ``MOREL_AUTH_TOKEN_READ`` gates the public endpoints ``/v1/complete`` and
  ``/v1/recommend``.
- ``MOREL_AUTH_TOKEN_ADMIN`` gates ``/v1/feedback``, ``/v1/rollback``, and
  ``/v1/stats``.

The legacy ``MOREL_AUTH_TOKEN`` variable is honored as a *read-scope*
fallback only. A migration that splits a single-tenant deployment into
READ and ADMIN tokens must explicitly set ``MOREL_AUTH_TOKEN_ADMIN`` —
otherwise admin routes stay locked, which is the only safe default for
state-mutating endpoints.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Callable
from typing import Literal

from fastapi import HTTPException, Request

from morel.core.errors import Cfg

Scope = Literal["read", "admin"]


def admin() -> bool:
    """Return whether admin-scope auth is configured.

    Admin scope only honors ``MOREL_AUTH_TOKEN_ADMIN``. The legacy
    ``MOREL_AUTH_TOKEN`` is **not** treated as an admin-scope
    credential so that a deployment that has only set the legacy
    variable cannot accidentally gain privileges on the state-mutating
    endpoints (``/v1/feedback``, ``/v1/rollback``, ``/v1/stats``).
    """
    return bool(os.environ.get("MOREL_AUTH_TOKEN_ADMIN"))


def viewer() -> bool:
    """Return whether read-scope auth is configured.

    Read scope is satisfied by either ``MOREL_AUTH_TOKEN_READ`` or the
    legacy ``MOREL_AUTH_TOKEN``. A deployment that has only configured
    the legacy single token continues to function for read endpoints,
    which is the original behaviour.
    """
    return bool(os.environ.get("MOREL_AUTH_TOKEN_READ") or os.environ.get("MOREL_AUTH_TOKEN"))


def token(scope: Scope) -> str | None:
    """Return the configured token for ``scope``, or ``None`` if auth is off.

    Admin scope falls back to *nothing*; read scope falls back to the
    legacy ``MOREL_AUTH_TOKEN``. See :func:`admin` and :func:`viewer`.
    """
    if scope == "admin":
        explicit = os.environ.get("MOREL_AUTH_TOKEN_ADMIN", "").strip()
    else:
        explicit = (
            os.environ.get("MOREL_AUTH_TOKEN_READ", "").strip()
            or os.environ.get("MOREL_AUTH_TOKEN", "").strip()
        )
        return explicit or None
    return explicit or None


def require(request: Request, scope: Scope = "read") -> None:
    """Validate the bearer token for the requested scope.

    No-op when no token is configured for ``scope``.

    Args
    ----
    request : Request
        Incoming FastAPI request.
    scope : Scope
        Which scope to enforce. ``"admin"`` for feedback/rollback/stats,
        ``"read"`` for complete/recommend.

    Raises
    ------
    HTTPException
        401 if the token is missing or wrong.
    """
    expected = token(scope)
    if not expected:
        return
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=f"missing bearer token for {scope}")
    presented = header.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=401, detail=f"invalid bearer token for {scope}")


def dependency(scope: Scope) -> Callable[[Request], None]:
    """Return a FastAPI-compatible dependency callable for the given scope.

    The returned callable preserves the ``(request: Request) -> None``
    signature so FastAPI can introspect the parameter list and inject the
    incoming request.
    """

    def scoped(request: Request) -> None:
        """FastAPI dependency that checks the required scope.

        Args:
            request: Incoming HTTP request.
        """
        require(request, scope=scope)

    return scoped


def assert_() -> None:
    """Raise if a deployment attempted to enable auth without setting any token."""
    if os.environ.get("MOREL_AUTH_ENABLED") == "1" and not (admin() or viewer()):
        raise Cfg("MOREL_AUTH_ENABLED=1 requires MOREL_AUTH_TOKEN[_READ|_ADMIN]")


__all__ = [
    "Scope",
    "admin",
    "assert_",
    "dependency",
    "require",
    "token",
    "viewer",
]
