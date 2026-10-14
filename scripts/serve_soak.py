"""Run a bounded concurrent HTTP soak against the real two-worker server."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from serve_workers_smoke import environment, wait_for_health


def fetch(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    timeout: float = 5,
) -> int:
    """Return the HTTP status, including expected error responses."""
    request = Request(
        url,
        data=body,
        headers={
            "Authorization": "Bearer smoke-read-token-123456",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status
    except HTTPError as exc:
        return exc.code
    except OSError as exc:
        raise RuntimeError(str(exc)) from exc


def main() -> int:
    """Run concurrent health, readiness, and malformed-request probes."""
    port = int(os.environ.get("MOREL_SOAK_PORT", "18114"))
    duration = float(os.environ.get("MOREL_SOAK_SECONDS", "10"))
    workers = int(os.environ.get("MOREL_SOAK_CLIENTS", "4"))
    interval = float(os.environ.get("MOREL_SOAK_INTERVAL", "0.25"))
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
    counts: dict[int, int] = {}
    errors: list[str] = []

    requests = [
        (f"{base}/health", "GET", None),
        (f"{base}/health/ready", "GET", None),
        (f"{base}/v1/complete", "POST", b"not-json"),
        # An empty item list fails at schema validation. A valid item
        # would intentionally wait for the model-loader timeout in this
        # no-bundle smoke, which is not useful for a bounded soak.
        (f"{base}/v1/complete", "POST", json.dumps({"items": []}).encode()),
    ]

    def probe(url: str, method: str, body: bytes | None) -> None:
        """Exercise one bounded process-level request path."""
        try:
            status = fetch(url, method=method, body=body)
        except Exception as exc:
            errors.append(f"{method} {url}: {exc}")
            return
        counts[status] = counts.get(status, 0) + 1

    output = ""
    try:
        status, _ = wait_for_health(base)
        if status != 200:
            raise RuntimeError(f"unexpected liveness status: {status}")
        # The supervisor can expose one worker before the second worker has
        # completed import/startup. Require a stable warm-up window before
        # measuring steady-state behavior.
        stable = 0
        warmup_deadline = time.monotonic() + 15.0
        while stable < 10 and time.monotonic() < warmup_deadline:
            try:
                if fetch(f"{base}/health", timeout=1) == 200:
                    stable += 1
                else:
                    stable = 0
            except Exception:
                stable = 0
            time.sleep(0.1)
        if stable < 10:
            raise RuntimeError("two-worker server did not reach a stable liveness window")
        deadline = time.monotonic() + duration
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while time.monotonic() < deadline:
                futures = [pool.submit(probe, *request) for request in requests]
                for future in futures:
                    try:
                        future.result()
                    except Exception as exc:  # pragma: no cover - process/network fault
                        errors.append(str(exc))
                time.sleep(interval)
        if errors:
            raise RuntimeError(f"soak probes failed: {errors[:3]}")
        expected = {200, 401, 422, 429, 503}
        unexpected = set(counts) - expected
        if unexpected:
            raise RuntimeError(f"unexpected statuses: {sorted(unexpected)}")
        print(json.dumps({"seconds": duration, "clients": workers, "statuses": counts}))
        return 0
    finally:
        process.terminate()
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        if errors and output:
            lines = output.splitlines()
            print("\n".join(lines[-40:]), file=sys.stderr)
        if process.returncode not in {0, -15}:
            raise RuntimeError(f"soak server exited {process.returncode}:\n{output}")


if __name__ == "__main__":
    raise SystemExit(main())
