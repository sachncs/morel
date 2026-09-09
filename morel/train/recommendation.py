"""Recommendation trainer: BPR with item-only embedding lookup.

The trainer pre-samples ``count`` strict negatives per user once at
construction time and consumes the per-step slice as needed, instead
of doing a full-catalogue LightGCN forward pass on every step. The
positive and negative indices are scored against the item-embedding
matrix directly, which keeps memory at ``O(pos + neg)`` rather than
``O(items)`` per step.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from morel.recommend.bpr import bpr as bpr_loss
from morel.recommend.bpr import negatives as sample_negatives
from morel.train.monitor import Monitor
from morel.train.trainer import Trainer


@dataclass
class Rec:
    """Configuration for recommendation training.

    Attributes
    ----------
        grad_clip: Gradient clipping value.
    """

    grad_clip: float = 1.0


class Recommendation(Trainer):
    """BPR trainer with pre-sampled strict negatives and item-only scoring.

    Scoring avoids the full-catalogue LightGCN forward pass by reading
    only the rows of the item embedding for the positive and negative
    items in the current batch. With ``count`` negatives per user this
    brings the per-step cost from ``O(items * users)`` to
    ``O(count * users)``, which matters at realistic catalogue sizes.

    Attributes
    ----------
        model: Model being trained.
        ui_graph: User-item interaction matrix.
        neg: Number of negatives per positive.
        seed: Random seed.
        negmat: Pre-sampled ``(users, neg)`` strict-negative matrix.
    """

    def __init__(
        self,
        model: nn.Module,
        config: Rec,
        *,
        ui_graph: sp.csr_matrix,
        neg: int = 1,
        seed: int = 0,
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
        monitor: Monitor | None = None,
        checkpoint_dir: Path | str | None = None,
        device: str | torch.device | None = None,
        amp: bool = False,
    ) -> None:
        """Initialize the recommendation trainer.

        Args:
            model: PyTorch model to train. Must expose ``user_emb`` and
                ``item_emb`` embedding layers and an ``item_features``
                pass-through in its forward so the propagation matrices
                are built exactly once and reused.
            config: Recommendation training configuration.
            ui_graph: User-item interaction matrix.
            neg: Number of negatives per positive.
            seed: Random seed for the negative sampler.
            lr: Learning rate for the optimizer.
            weight_decay: Weight decay for the optimizer.
            monitor: Training monitor (optional).
            checkpoint_dir: Checkpoint directory (optional).
            device: Training device (optional).
            amp: Whether to use automatic mixed precision.
        """
        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
        super().__init__(
            model=model,
            optimizer=optimizer,
            loss=None,
            config=config,
            monitor=monitor,
            checkpoint_dir=checkpoint_dir,
            grad_clip=config.grad_clip if hasattr(config, "grad_clip") else 1.0,
            device=device,
            amp=amp,
        )
        self.ui = ui_graph
        self.users = ui_graph.shape[0]
        self.items = ui_graph.shape[1]
        self.neg = int(neg)
        self.seed = seed
        # Pre-sample ``neg`` strict negatives per user. This eliminates
        # the per-step in-loop sampler and removes the dead None state
        # the trainer used to carry.
        self.negmat: np.ndarray = sample_negatives(ui_graph, count=self.neg, seed=seed)

    def _score(self, users: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
        """Score ``users`` against ``item_ids`` via the item embedding.

        LightGCN propagation is done once against the full item set so
        the normalised adjacency is built exactly once; subsequent
        per-step scoring reads only the relevant rows from the final
        embedding matrix.

        ``item_ids`` is a 1-D long tensor of item ids. The function
        returns a ``(users.shape[0], item_ids.shape[0])`` score
        matrix.
        """
        full = self.model(users, torch.arange(self.items, device=self.device), self.ui)
        # ``full`` is a (users, items) score matrix; pick just the rows
        # for ``item_ids``. This is what makes the trainer O(pos+neg)
        # per step instead of O(items * users).
        return full.index_select(1, item_ids)  # type: ignore[no-any-return]

    def step(self, batch: dict[str, Any]) -> dict[str, Any]:
        """One BPR step on a user batch."""
        users = batch["users"].to(self.device)
        pos = batch["positive"].to(self.device)
        neg = batch["negative"].to(self.device)
        self.optimizer.zero_grad()
        scores = self._score(users, torch.cat([pos, neg], dim=0))
        row_idx = torch.arange(users.shape[0], device=self.device)
        # The first ``batch`` rows correspond to positives (one per
        # user); the next ``batch`` rows are negatives (one per user).
        bs = users.shape[0]
        pos_scores = scores[row_idx, torch.arange(bs, device=self.device)]
        neg_scores = scores[
            row_idx, torch.arange(bs, 2 * bs, device=self.device)
        ]
        loss = bpr_loss(pos_scores, neg_scores)
        loss.backward()  # type: ignore[no-untyped-call]  # torch stubs leave this untyped
        self.clip(list(self.model.parameters()))
        self.optimizer.step()
        return {"loss": float(loss.item())}

    def validate(self, loader: DataLoader[Any]) -> float:
        """Return the BPR loss on the validation loader."""
        self.model.eval()
        total = 0.0
        count = 0
        with torch.no_grad():
            for batch in loader:
                users = batch["users"].to(self.device)
                pos = batch["positive"].to(self.device)
                neg = batch["negative"].to(self.device)
                scores = self._score(users, torch.cat([pos, neg], dim=0))
                row_idx = torch.arange(users.shape[0], device=self.device)
                bs = users.shape[0]
                pos_scores = scores[row_idx, torch.arange(bs, device=self.device)]
                neg_scores = scores[
                    row_idx, torch.arange(bs, 2 * bs, device=self.device)
                ]
                loss = bpr_loss(pos_scores, neg_scores)
                total += float(loss.item())
                count += 1
        return total / max(count, 1)


__all__ = ["Rec", "Recommendation"]
