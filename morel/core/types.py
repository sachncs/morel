"""Core dataclasses shared across morel.

Every domain module imports its primitives from here. This module
imports nothing from morel.

The previous ``Modality``, ``Mask``, and ``Graph`` Protocols lived in
this module but were never referenced outside it and
:mod:`morel.core`. Worse, the ``Mask`` Protocol's shape did not match
the concrete ``Mask`` dataclass in :mod:`morel.data.mask`, so a caller
that did try to use them hit a structural-typecheck failure.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class Embedding:
    """Tensor wrapper that exposes shape, dtype, device explicitly.

    Carries a single torch tensor with its semantic name. Used at module
    boundaries to make data flow auditable.

    Attributes
    ----------
        name: Semantic name of the tensor.
        tensor: The wrapped torch tensor.
    """

    name: str
    tensor: torch.Tensor

    @property
    def shape(self) -> torch.Size:
        """Return the shape of the underlying tensor."""
        return self.tensor.shape

    @property
    def dtype(self) -> torch.dtype:
        """Return the dtype of the underlying tensor."""
        return self.tensor.dtype

    @property
    def device(self) -> torch.device:
        """Return the device of the underlying tensor."""
        return self.tensor.device

    @property
    def grad(self) -> bool:
        """Return whether the underlying tensor has a gradient."""
        return self.tensor.grad is not None

    def to(self, device: torch.device | str) -> Embedding:
        """Return a new Embedding on the given device."""
        return Embedding(name=self.name, tensor=self.tensor.to(device))


__all__ = ["Embedding"]
