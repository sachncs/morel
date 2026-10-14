"""Acquisition: download remote datasets with retries, timeouts, and checksums."""

from __future__ import annotations

import gzip
import os
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from morel.core.errors import Datum

TIMEOUT = 60
RETRIES = 3
BACKOFF = 1.5
AGENT = "morel/0.1"
MAX_DOWNLOAD_BYTES = 1 << 30
MAX_DECOMPRESSED_BYTES = 1 << 31

BASE = "https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_v2/categoryFilesSmall/"


def fetch(
    url: str,
    dest: Path | str,
    *,
    timeout: float = TIMEOUT,
    retries: int = RETRIES,
    backoff: float = BACKOFF,
    sha: str | None = None,
    progress: Callable[[int, int | None], None] | None = None,
    max_bytes: int = MAX_DOWNLOAD_BYTES,
) -> Path:
    """Fetch a remote URL to a local file with retries and optional checksum.

    Args:
        url: HTTPS URL.
        dest: Local destination path.
        timeout: Per-attempt timeout in seconds.
        retries: Number of retries after the first failure.
        backoff: Exponential backoff factor between attempts.
        sha: Optional SHA256 expected digest; raises Datum on mismatch.
        progress: Optional callback ``(bytes_done, total_bytes_or_None)``.
        max_bytes: Maximum response body size accepted.

    Returns:
        The destination path.

    Raises:
        Datum: If the URL cannot be fetched, or the checksum mismatches.
    """
    target = Path(dest).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise Datum(f"max_bytes must be positive, got {max_bytes!r}")
    attempt = 0
    last_error: Exception | None = None
    while attempt <= retries:
        try:
            fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        except OSError as exc:
            raise Datum(f"unable to create temporary download for {target}") from exc
        try:
            request = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with (
                os.fdopen(fd, "wb") as out,
                urllib.request.urlopen(request, timeout=timeout) as response,
            ):
                total = response.length
                if isinstance(total, int) and total > max_bytes:
                    raise Datum(f"download from {url} exceeds the {max_bytes}-byte limit")
                done = 0
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    if done + len(chunk) > max_bytes:
                        raise Datum(f"download from {url} exceeds the {max_bytes}-byte limit")
                    out.write(chunk)
                    done += len(chunk)
                    if progress is not None:
                        progress(done, total)
            if sha is not None:
                from morel.data.manifest import checksum

                temporary_path = Path(temporary)
                if checksum(temporary_path) != sha:
                    raise Datum(
                        f"checksum mismatch for {target}: expected {sha}, "
                        f"got {checksum(temporary_path)}"
                    )
            os.replace(temporary, target)
            return target
        except Datum:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            attempt += 1
            if attempt > retries:
                break
            time.sleep(backoff**attempt)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
    raise Datum(f"failed to fetch {url} after {retries + 1} attempts: {last_error}")


def pull(
    base: str,
    category: str,
    dest: Path | str,
    *,
    timeout: float,
    max_decompressed_bytes: int = MAX_DECOMPRESSED_BYTES,
) -> list[Path]:
    """Download and decompress the dataset files.

    Args:
        base: Base URL for the dataset.
        category: Dataset category name.
        dest: Local destination directory.
        timeout: Download timeout in seconds.
        max_decompressed_bytes: Maximum decompressed file size accepted.

    Returns:
        list[Path]: Paths to the decompressed files.
    """
    files = [f"{category}_5.json.gz", f"{category}_metadata.json.gz"]
    root = Path(dest).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if (
        isinstance(max_decompressed_bytes, bool)
        or not isinstance(max_decompressed_bytes, int)
        or max_decompressed_bytes <= 0
    ):
        raise Datum(f"max_decompressed_bytes must be positive, got {max_decompressed_bytes!r}")
    decompressed: list[Path] = []
    for fname in files:
        archive = root / fname
        final = archive.with_suffix("")
        if final.exists():
            decompressed.append(final)
            continue
        fetch(base + fname, archive, timeout=timeout)
        fd, temporary = tempfile.mkstemp(prefix=f".{final.name}.", dir=root)
        try:
            done = 0
            with gzip.open(archive, "rb") as src, os.fdopen(fd, "wb") as out:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    if done + len(chunk) > max_decompressed_bytes:
                        raise Datum(
                            f"decompressed {archive} exceeds the "
                            f"{max_decompressed_bytes}-byte limit"
                        )
                    out.write(chunk)
                    done += len(chunk)
            os.replace(temporary, final)
            os.remove(archive)
        except Datum:
            raise
        except (OSError, EOFError, gzip.BadGzipFile) as exc:
            raise Datum(f"unable to decompress dataset archive: {archive}") from exc
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        decompressed.append(final)
    return decompressed


def download(category: str, dest: Path | str, *, timeout: float = TIMEOUT) -> list[Path]:
    """Download Amazon 5-core review and metadata for a category.

    Defaults to the Amazon-Reviews-2023 mirror. Raises an actionable
    :class:`Datum` if the mirror is unreachable.

    Args:
        category: Amazon category slug (e.g. ``"Beauty"``).
        dest: Destination directory.
        timeout: Per-attempt download timeout.

    Returns:
        The list of decompressed file paths.
    """
    return pull(BASE, category, dest, timeout=timeout)


__all__ = [
    "BACKOFF",
    "BASE",
    "MAX_DECOMPRESSED_BYTES",
    "MAX_DOWNLOAD_BYTES",
    "RETRIES",
    "TIMEOUT",
    "download",
    "fetch",
]
