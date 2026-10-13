"""Run a bounded concurrent HTTP soak against the real two-worker server."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from serve_workers_smoke import environment, wait_for_health


def fetch(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    timeout: float = 5,
) -> int:
    """Return the HTTP status, including expected error responses."""
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--http1.1",
        "--output",
        "/dev/null",
        "--write-out",
        "%{http_code}",
        "--max-time",
        str(timeout),
        "-X",
        method,
        "-H",
        "Authorization: Bearer smoke-read-token-123456",
        "-H",
        "Content-Type: application/json",
        url,
    ]
    if body is not None:
        command.extend(["--data-binary", body.decode("utf-8")])
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(str(exc)) from exc
    return int(result.stdout)


def main() -> int:
    """Run concurrent health, readiness, and malformed-request probes."""
    port = int(os.environ.get("MOREL_SOAK_PORT", "18114"))
    duration = float(os.environ.get("MOREL_SOAK_SECONDS", "10"))
    workers = int(os.environ.get("MOREL_SOAK_CLIENTS", "8"))
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
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    counts: dict[int, int] = {}
    errors: list[str] = []

    def probe() -> None:
        """Exercise all bounded process-level request paths once."""
        requests = [
            (f"{base}/health", "GET", None),
            (f"{base}/health/ready", "GET", None),
            (f"{base}/v1/complete", "POST", b"not-json"),
            (f"{base}/v1/complete", "POST", json.dumps({"items": [0]}).encode()),
        ]
        for url, method, body in requests:
            try:
                status = fetch(url, method=method, body=body)
            except Exception as exc:
                errors.append(f"{method} {url}: {exc}")
                continue
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
                futures = [pool.submit(probe) for _ in range(workers)]
                for future in futures:
                    try:
                        future.result()
                    except Exception as exc:  # pragma: no cover - process/network fault
                        errors.append(str(exc))
                time.sleep(0.1)
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
            print(output, file=sys.stderr)
        if process.returncode not in {0, -15}:
            raise RuntimeError(f"soak server exited {process.returncode}:\n{output}")


if __name__ == "__main__":
    raise SystemExit(main())
