"""Exercise model-backed serving through the real multi-worker HTTP path."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from serve_workers_smoke import environment


def fetch(base: str, path: str, body: Mapping[str, object] | None = None) -> tuple[int, object]:
    """Fetch one JSON endpoint with the local production-like credentials."""
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        base + path,
        data=payload,
        method="POST" if payload is not None else "GET",
        headers={
            "Authorization": "Bearer smoke-read-token-123456",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            return int(response.status), json.loads(response.read())
    except HTTPError as exc:
        return int(exc.code), json.loads(exc.read())
    except URLError as exc:
        raise RuntimeError(str(exc)) from exc


def main() -> int:
    """Start workers with a real checkpoint and verify inference responses."""
    port = int(os.environ.get("MOREL_MODEL_SMOKE_PORT", "18116"))
    model_dir = os.environ.get("MOREL_MODEL_SMOKE_DIR", "runs/completion")
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
        "--model-dir",
        model_dir,
    ]
    process = subprocess.Popen(
        command,
        env=environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            try:
                if fetch(base, "/health")[0] == 200:
                    break
            except RuntimeError:
                pass
            time.sleep(0.25)
        else:
            raise RuntimeError("model-backed server did not start")

        probes = {
            "/health": (None, 200),
            "/health/ready": (None, 200),
            "/v1/complete": ({"items": [0, 1]}, 200),
            "/v1/recommend": ({"user": 0, "top": 3}, 200),
        }
        results: dict[str, object] = {}
        for path, (body, expected) in probes.items():
            status, response = fetch(base, path, body)
            if status != expected:
                raise RuntimeError(f"{path} returned {status}, expected {expected}: {response}")
            results[path] = response
        ready = results["/health/ready"]
        recommendation = results["/v1/recommend"]
        if not isinstance(ready, dict) or ready.get("status") != "ready":
            raise RuntimeError(f"readiness response was not ready: {ready}")
        if not isinstance(recommendation, dict) or not recommendation.get("items"):
            raise RuntimeError(f"recommendation response was empty: {recommendation}")
        print(json.dumps({"model_dir": model_dir, "probes": list(results)}))
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        if process.returncode not in {0, -15}:
            raise RuntimeError(f"model smoke server exited {process.returncode}")


if __name__ == "__main__":
    raise SystemExit(main())
