"""Modality-agnostic feature extractors.

A single ``Feature`` Protocol covers text and visual encoders.
Implementations are responsible for producing L2-normalized ``float32``
arrays of shape ``(items, dim)``.
"""

from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from torchvision import models as tv_models

from morel.core.errors import Datum
from morel.core.log import get as logger

log = logger("data.extract")


class Feature(Protocol):
    """One feature extractor for raw modality inputs.

    Attributes
    ----------
        forward: Returns per-item feature vectors.
    """

    name: str
    dim: int

    def encode(self, inputs: list[str], *, device: str | torch.device | None = None) -> np.ndarray:
        """Encode a batch of inputs to ``(len(inputs), self.dim)`` float32."""
        ...


def l2_normalize(array: np.ndarray) -> np.ndarray:
    """L2-normalize each row; replace zero-norm rows with the zero vector."""
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    safe = np.where(norms == 0.0, 1.0, norms)
    return (array / safe).astype(np.float32, copy=False)


def text(
    inputs: list[str],
    encoder: Feature,
    *,
    batch: int = 64,
    device: str | torch.device | None = None,
) -> np.ndarray:
    """Encode text inputs through any Feature implementation.

    Args:
        inputs: List of strings.
        encoder: A text or multimodal encoder.
        batch: Batch size.
        device: Device override.

    Returns
    -------
        Array of shape ``(len(inputs), encoder.dim)``, L2-normalized, float32.
    """
    if not inputs:
        raise Datum("text encoder received empty input list")
    return encoder.encode(inputs, device=device)


def visual(
    paths: list[str],
    encoder: Feature,
    *,
    batch: int = 32,
    device: str | torch.device | None = None,
) -> tuple[np.ndarray, list[int]]:
    """Encode image paths through any Feature implementation.

    Falls back to per-path encoding whenever the batched ``encoder.encode``
    call raises an ``OSError`` (missing path, permission, broken image
    link) or an ``UnidentifiedImageError`` from PIL. The returned
    ``kept_indices`` lists positions in the original ``paths`` that
    decoded successfully, and the returned ``features`` has
    ``shape[0] == len(kept_indices)``.

    Args:
        paths: List of filesystem paths to images.
        encoder: A visual encoder.
        batch: Batch size.
        device: Device override.

    Returns
    -------
        Tuple of ``(features, kept_indices)`` where ``features`` is
        ``(len(kept), encoder.dim)`` L2-normalized float32 and ``kept_indices``
        are positions in the original ``paths`` that succeeded.
    """
    if not paths:
        raise Datum("visual encoder received empty input list")
    try:
        return encoder.encode(paths, device=device), list(range(len(paths)))
    except (OSError, ValueError) as primary_exc:
        log.warning(
            "visual.batched_encode_failed; falling back to per-path",
            extra={"error": str(primary_exc), "n_paths": len(paths)},
        )
        kept: list[int] = []
        rows: list[np.ndarray] = []
        for idx, path in enumerate(paths):
            try:
                row = encoder.encode([path], device=device)
            except (OSError, ValueError) as path_exc:
                log.warning(
                    "visual.skip_unreadable",
                    extra={"path": path, "error": str(path_exc)},
                )
                continue
            kept.append(idx)
            rows.append(row)
        if not rows:
            raise Datum(
                f"visual encoder could not decode any of {len(paths)} paths; "
                f"original error: {primary_exc}"
            ) from primary_exc
        return np.vstack(rows), kept


def random(items: int, dim: int, *, seed: int, name: str = "random") -> np.ndarray:
    """Deterministic random L2-normalized features.

    Used in tests, demos, and as a fallback when real encoders are unavailable.
    """
    if items <= 0:
        raise Datum(f"items must be positive, got {items}")
    if dim <= 0:
        raise Datum(f"dim must be positive, got {dim}")
    rng = np.random.default_rng(seed)
    array = rng.normal(size=(items, dim)).astype(np.float32)
    return l2_normalize(array)


class Random:
    """Deterministic pseudo-random encoder.

    Satisfies :class:`Feature` without any model download, so the
    synthetic pipeline exercises the same code path as a real encoder.

    Attributes
    ----------
        name: Extractor name.
        dim: Output feature dimension.
        seed: Random seed.
    """

    def __init__(self, dim: int, *, seed: int = 0, name: str = "random") -> None:
        """Build an encoder producing ``dim``-wide rows."""
        if dim <= 0:
            raise Datum(f"dim must be positive, got {dim}")
        self.name = name
        self.dim = dim
        self.seed = seed

    def encode(self, inputs: list[str], *, device: str | torch.device | None = None) -> np.ndarray:
        """Encode each input to a row derived from its text, not its position.

        Deriving the row from a hash of the input keeps the output stable when
        the same item appears at a different index or in a different batch.
        """
        del device
        rows = np.empty((len(inputs), self.dim), dtype=np.float32)
        for i, item in enumerate(inputs):
            digest = hashlib.sha256(f"{self.seed}:{item}".encode()).digest()
            local = np.random.default_rng(int.from_bytes(digest[:8], "little"))
            rows[i] = local.normal(size=self.dim).astype(np.float32)
        return l2_normalize(rows)


class Sentence:
    """Text encoder backed by sentence-transformers.

    Attributes
    ----------
        name: Model name.
        batch: Batch size for encoding.
        model: Underlying SentenceTransformer model.
        dim: Output feature dimension.
    """

    def __init__(self, model: str, *, batch: int = 64) -> None:
        """Load ``model``; requires the ``text`` extra."""
        self.name = model
        self.batch = batch
        self.model = SentenceTransformer(model)
        self.dim = int(self.model.get_sentence_embedding_dimension())

    def encode(  # pragma: no cover - requires a model download
        self, inputs: list[str], *, device: str | torch.device | None = None
    ) -> np.ndarray:
        """Encode text through the loaded sentence-transformer."""
        vectors = self.model.encode(
            inputs, batch_size=self.batch, convert_to_numpy=True, device=device
        )
        return l2_normalize(np.asarray(vectors, dtype=np.float32))


class Vision:
    """Visual encoder backed by a torchvision classification backbone.

    Attributes
    ----------
        name: Model name.
        batch: Batch size for encoding.
        model: Underlying torchvision model.
        dim: Output feature dimension.
    """

    def __init__(self, model: str, *, batch: int = 32) -> None:
        """Load ``model`` with default pretrained weights; requires ``vision``."""
        builder = getattr(tv_models, model, None)
        if builder is None:
            raise Datum(f"torchvision has no model named {model!r}")
        self.name = model
        self.batch = batch
        # Probe the model with weights=None to read the actual output
        # dimension of the final fully-connected layer. This costs an
        # extra constructor call but is the only way to learn the
        # dimension for arbitrary backbones; we discard the
        # weights=None probe after reading ``fc.in_features``.
        probe = builder(weights=None)
        feature_dim = int(probe.fc.in_features)
        del probe
        self.model = builder(weights="DEFAULT")
        self.model.fc = torch.nn.Identity()
        self.model.eval()
        self.dim = feature_dim

    def encode(  # pragma: no cover - requires a model download
        self, inputs: list[str], *, device: str | torch.device | None = None
    ) -> np.ndarray:
        """Encode image paths through the loaded backbone."""
        from PIL import Image
        from torchvision import transforms

        prep = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        batch = torch.stack([prep(Image.open(path).convert("RGB")) for path in inputs])
        with torch.no_grad():
            out = self.model(batch.to(device) if device else batch)
        return l2_normalize(out.cpu().numpy().astype(np.float32))


def fingerprint(payload: np.ndarray) -> str:
    """Stable SHA256 of an array's bytes (used for manifest binding)."""
    return hashlib.sha256(np.ascontiguousarray(payload).tobytes()).hexdigest()


__all__ = [
    "Feature",
    "Random",
    "Sentence",
    "Vision",
    "fingerprint",
    "l2_normalize",
    "random",
    "text",
    "visual",
]
