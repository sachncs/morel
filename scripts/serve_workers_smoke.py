"""Exercise the local two-worker serving lifecycle without a model bundle."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def fetch(url: str) -> tuple[int, str]:
    """Fetch a JSON health endpoint and return status plus body."""
    try:
        with urlopen(url, timeout=2) as response:
            return int(response.status), response.read().decode("utf-8")
    except HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8")
    except URLError as exc:
        raise RuntimeError(str(exc)) from exc


def wait_for_health(base: str, *, timeout: float = 15.0) -> tuple[int, str]:
    """Wait until the local process exposes liveness or fail with logs."""
    deadline = time.monotonic() + timeout
    last_error = "server did not start"
    while time.monotonic() < deadline:
        try:
            status, body = fetch(f"{base}/health")
            if status == 200:
                return status, body
        except RuntimeError as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise RuntimeError(last_error)


def environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build an isolated production-like environment for the smoke process."""
    values = dict(os.environ if source is None else source)
    values.update(
        {
            "MOREL_ENV": "production",
            "MOREL_AUTH_TOKEN_READ": "smoke-read-token-123456",
            "MOREL_AUTH_TOKEN_ADMIN": "smoke-admin-token-654321",
        }
    )
    return values


def main() -> int:
    """Start two workers, probe lifecycle endpoints, and shut them down."""
    port = int(os.environ.get("MOREL_SMOKE_PORT", "18113"))
    base = f"http://127.0.0.1:{port}"
    command = [
        sys.executable,
        "-m",
        "morel",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--workers",
        "2",
    ]
    process = subprocess.Popen(
        command,
        env=environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = ""
    try:
        status, body = wait_for_health(base)
        if status != 200:
            raise RuntimeError(f"unexpected liveness status: {status}")
        ready_status, ready_body = fetch(f"{base}/health/ready")
        if ready_status != 503:
            raise RuntimeError(f"expected readiness 503 without a bundle, got {ready_status}")
        for _ in range(20):
            health_status, _ = fetch(f"{base}/health")
            if health_status != 200:
                raise RuntimeError(f"liveness degraded to {health_status}")
        print(json.dumps({"health": json.loads(body), "ready_status": ready_status}))
        print(ready_body)
        return 0
    finally:
        process.terminate()
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        if process.returncode not in {0, -15}:
            raise RuntimeError(f"worker smoke exited {process.returncode}:\n{output}")


if __name__ == "__main__":
    raise SystemExit(main())
