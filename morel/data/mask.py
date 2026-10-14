"""Modality availability masks.

A mask is a 2-D binary array of shape ``(items, modalities)`` where ``1``
means "kept" and ``0`` means "missing". Every item is guaranteed to have at
least one kept modality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from morel.core.errors import Datum
from morel.core.types import Array


@runtime_checkable
class Spec(Protocol):
    """Factory for mask arrays.

    Attributes:
        sample: Returns a sampled binary mask.
    """

    def sample(self, items: int, modalities: int, *, seed: int) -> Array:
        """Sample a binary mask of shape ``(items, modalities)``."""
        ...


@dataclass(frozen=True)
class ModalityMask:
    """Immutable value object describing modality availability.

    Attributes:
        data: Binary mask array of shape ``(items, modalities)``.
    """

    data: Array

    def __post_init__(self) -> None:
        """Validate the mask data on construction."""
        if self.data.ndim != 2:
            raise Datum(f"mask must be 2-D, got {self.data.ndim}-D")
        if self.data.shape[0] == 0:
            raise Datum("mask has no items")
        if not np.all(np.isin(self.data, [0.0, 1.0])):
            raise Datum("mask values must be 0 or 1")
        if (self.data.sum(axis=1) == 0).any():
            raise Datum("mask rows must keep at least one modality")

    @property
    def items(self) -> int:
        """Return the number of items."""
        return int(self.data.shape[0])

    @property
    def modalities(self) -> int:
        """Return the number of modalities."""
        return int(self.data.shape[1])

    def kept(self, item: int) -> Array:
        """Return which modalities are kept for a given item."""
        kept: Array = self.data[item] > 0
        return kept

    def missing(self, item: int) -> Array:
        """Return which modalities are missing for a given item."""
        absent: Array = self.data[item] == 0
        return absent

    def numpy(self) -> Array:
        """Return the underlying array."""
        return self.data


def bernoulli(items: int, modalities: int, ratio: float, *, seed: int) -> ModalityMask:
    """Independent Bernoulli masking with at-least-one repair.

    Args:
        items: Number of items.
        modalities: Number of modalities.
        ratio: Probability of masking per (item, modality) pair.
        seed: Random seed.

    Returns:
        A ``ModalityMask`` with shape ``(items, modalities)``.
    """
    if not 0.0 <= ratio <= 1.0:
        raise Datum(f"ratio must be in [0, 1], got {ratio}")
    if items <= 0 or modalities <= 0:
        raise Datum("items and modalities must be positive")
    rng = np.random.default_rng(seed)
    base = (rng.random((items, modalities)) > ratio).astype(np.float32)
    # Vectorized repair: rows with no kept modality get the first one set.
    rowsums = base.sum(axis=1)
    needs_repair = rowsums == 0
    if needs_repair.any():
        first_keep = np.argmax(base[needs_repair] == 1, axis=1)
        # If a row is entirely zero, force-keep modality 0.
        no_kept = base[needs_repair].sum(axis=1) == 0
        first_keep = np.where(no_kept, 0, first_keep)
        rows = np.where(needs_repair)[0]
        base[rows, first_keep] = 1.0
    return ModalityMask(data=base)


def block(items: int, modalities: int, block_size: int, *, seed: int) -> ModalityMask:
    """Block masking: contiguous modality spans are masked together.

    Args:
        items: Number of items.
        modalities: Number of modalities.
        block_size: Length of each block.
        seed: Random seed.

    Returns:
        A ``ModalityMask``.
    """
    if block_size <= 0 or block_size > modalities:
        raise Datum(f"block_size must be in [1, {modalities}], got {block_size}")
    rng = np.random.default_rng(seed)
    base = np.ones((items, modalities), dtype=np.float32)
    for i in range(items):
        start = int(rng.integers(0, modalities - block_size + 1))
        base[i, start : start + block_size] = 0.0
    return ModalityMask(data=base)


def structured(pattern: Array) -> ModalityMask:
    """Use a fixed pattern (e.g. ground-truth modality availability) as the mask.

    Args:
        pattern: 2-D binary array of shape ``(items, modalities)``.

    Returns:
        A ``ModalityMask``.
    """
    pattern = pattern.astype(np.float32, copy=False)
    return ModalityMask(data=pattern)


def stack(masks: list[ModalityMask]) -> Array:
    """Stack a list of masks into a 3-D array ``(len(masks), items, modalities)``."""
    if not masks:
        raise Datum("stack requires at least one mask")
    arrays = [m.numpy() for m in masks]
    return np.stack(arrays, axis=0)


# Compatibility alias for callers of the original public name. New code should
# use ModalityMask to distinguish this value object from configuration/protocol
# concepts that describe masking behavior.
Mask = ModalityMask


__all__ = ["Mask", "ModalityMask", "Spec", "bernoulli", "block", "stack", "structured"]
