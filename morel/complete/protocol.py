"""Runtime contract for modality completion stages."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import torch


@runtime_checkable
class Completer(Protocol):
    """Stage that decodes a latent representation into modality tensors."""

    def forward(
        self,
        latent: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        """Decode one latent batch into per-modality outputs."""


__all__ = ["Completer"]
