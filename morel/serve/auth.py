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
from pathlib import Path
from typing import Literal

from fastapi import HTTPException, Request

from morel.core.errors import Cfg

Scope = Literal["read", "admin"]
_MAX_SECRET_BYTES = 4096


def _secret(scope: Scope) -> str | None:
    """Resolve a scope token from a direct value or a mounted secret file."""
    if scope == "admin":
        direct_name = "MOREL_AUTH_TOKEN_ADMIN"
        file_name = "MOREL_AUTH_TOKEN_ADMIN_FILE"
    else:
        direct_name = "MOREL_AUTH_TOKEN_READ"
        file_name = "MOREL_AUTH_TOKEN_READ_FILE"
    direct = os.environ.get(direct_name, "").strip()
    file_path = os.environ.get(file_name, "").strip()
    if direct and file_path:
        raise Cfg(f"set only one of {direct_name} or {file_name}")
    if not file_path:
        return direct or None
    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = handle.read(_MAX_SECRET_BYTES + 1).strip()
    except (OSError, UnicodeError) as exc:
        raise Cfg(f"unable to read {file_name} secret file") from exc
    if len(value.encode("utf-8")) > _MAX_SECRET_BYTES:
        raise Cfg(f"{file_name} secret exceeds {_MAX_SECRET_BYTES} bytes")
    if not value:
        raise Cfg(f"{file_name} secret file is empty")
    return value


def _legacy_secret() -> str | None:
    """Resolve the legacy read-only token and its file-reference variant."""
    direct = os.environ.get("MOREL_AUTH_TOKEN", "").strip()
    file_path = os.environ.get("MOREL_AUTH_TOKEN_FILE", "").strip()
    if direct and file_path:
        raise Cfg("set only one of MOREL_AUTH_TOKEN or MOREL_AUTH_TOKEN_FILE")
    if not file_path:
        return direct or None
    try:
        with Path(file_path).open("r", encoding="utf-8") as handle:
            value = handle.read(_MAX_SECRET_BYTES + 1).strip()
    except (OSError, UnicodeError) as exc:
        raise Cfg("unable to read MOREL_AUTH_TOKEN_FILE secret file") from exc
    if len(value.encode("utf-8")) > _MAX_SECRET_BYTES:
        raise Cfg(f"MOREL_AUTH_TOKEN_FILE secret exceeds {_MAX_SECRET_BYTES} bytes")
    if not value:
        raise Cfg("MOREL_AUTH_TOKEN_FILE secret file is empty")
    return value


def admin() -> bool:
    """Return whether admin-scope auth is configured.

    Admin scope only honors ``MOREL_AUTH_TOKEN_ADMIN``. The legacy
    ``MOREL_AUTH_TOKEN`` is **not** treated as an admin-scope
    credential so that a deployment that has only set the legacy
    variable cannot accidentally gain privileges on the state-mutating
    endpoints (``/v1/feedback``, ``/v1/rollback``, ``/v1/stats``).
    """
    return bool(_secret("admin"))


def viewer() -> bool:
    """Return whether read-scope auth is configured.

    Read scope is satisfied by either ``MOREL_AUTH_TOKEN_READ`` or the
    legacy ``MOREL_AUTH_TOKEN``. A deployment that has only configured
    the legacy single token continues to function for read endpoints,
    which is the original behaviour.
    """
    return bool(_secret("read") or _legacy_secret())


def token(scope: Scope) -> str | None:
    """Return the configured token for ``scope``, or ``None`` if auth is off.

    Admin scope falls back to *nothing*; read scope falls back to the
    legacy ``MOREL_AUTH_TOKEN``. See :func:`admin` and :func:`viewer`.
    """
    if scope == "admin":
        return _secret("admin")
    return _secret("read") or _legacy_secret()


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
        raise Cfg("MOREL_AUTH_ENABLED=1 requires a direct token or *_FILE secret reference")


def assert_production() -> None:
    """Require separate read and admin credentials in production mode.

    Development and test processes remain unauthenticated unless explicitly
    configured. A process declaring ``MOREL_ENV=production`` cannot silently
    expose model or state-mutating endpoints without both scopes configured.
    """
    if os.environ.get("MOREL_ENV", "").strip().lower() != "production":
        return
    read = token("read")
    admin_token = token("admin")
    if not read or not admin_token:
        raise Cfg("MOREL_ENV=production requires read and admin tokens or their *_FILE references")
    if len(read) < 16 or len(admin_token) < 16:
        raise Cfg("production auth tokens must each contain at least 16 characters")
    if hmac.compare_digest(read, admin_token):
        raise Cfg("production read and admin auth tokens must be different")


__all__ = [
    "Scope",
    "admin",
    "assert_",
    "assert_production",
    "dependency",
    "require",
    "token",
    "viewer",
]
