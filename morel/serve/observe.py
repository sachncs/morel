"""Pure ASGI request observation middleware."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from morel.serve.metrics import Registry, metrics_response

log = logging.getLogger("morel.serve.app")


class ObserveMiddleware:
    """Observe HTTP requests without swallowing cancellation signals."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        metrics_enabled: bool,
        metrics_path: str,
        request_id_factory: Callable[[str], str],
    ) -> None:
        """Configure request observation and metrics exposure."""
        self.app = app
        self.metrics_enabled = metrics_enabled
        self.metrics_path = metrics_path
        self.request_id_factory = request_id_factory

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Dispatch one ASGI scope and preserve cancellation semantics."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        headers = dict(scope.get("headers", ()))
        supplied = headers.get(b"x-request-id", b"").decode("latin-1")
        request_id = self.request_id_factory(supplied)
        state["request_id"] = request_id
        registry: Registry = scope["app"].state.metrics_registry
        started = time.perf_counter()
        status = 500

        async def observed_send(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
                raw_headers = list(message.get("headers", []))
                raw_headers = [
                    (key, value) for key, value in raw_headers if key.lower() != b"x-request-id"
                ]
                raw_headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": raw_headers}
            await send(message)

        try:
            if self.metrics_enabled and scope.get("path") == self.metrics_path:
                response = metrics_response(registry)
                response.headers["X-Request-ID"] = request_id
                await response(scope, receive, observed_send)
            else:
                await self.app(scope, receive, observed_send)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception(
                "unexpected serving failure",
                extra={"request_id": request_id, "path": scope.get("path", "")},
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": (
                            "unexpected serving failure; see server logs with the request id"
                        ),
                        "request_id": request_id,
                    }
                },
            )
            await response(scope, receive, observed_send)
        finally:
            registry.observe_request(
                endpoint=scope.get("path", ""),
                method=scope.get("method", ""),
                status=status,
                elapsed=max(0.0, time.perf_counter() - started),
            )


__all__ = ["ObserveMiddleware"]
