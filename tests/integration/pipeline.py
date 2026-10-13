"""Integration test: real Pipeline driven by Completion trainer."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp
import torch
from torch.utils.data import DataLoader

from morel.core.config import Config
from morel.core.errors import Model, Net
from morel.pipeline import Pipeline
from morel.train.completion import Completion, Fit
from tests.shared import Corpus, build_path_graph, make_completion_collate


class Monitor:
    """Test monitor that discards metric logs."""

    def log(self, step: int | None = None, **metrics: object) -> None:
        """Discard the call and accept any keyword arguments."""
        return


class Checker:
    """Aggregated test methods for this module."""

    def real(self, tmp_path) -> None:
        rng = np.random.default_rng(0)
        n = 30
        dv = 6
        dim_text = 4
        features_np = {
            "visual": rng.normal(size=(n, dv)).astype(np.float32),
            "text": rng.normal(size=(n, dim_text)).astype(np.float32),
        }
        mask_np = np.ones((n, 2), dtype=np.float32)
        adj = build_path_graph(n)

        config = Config()
        pipeline = Pipeline(config, dims={"visual": dv, "text": dim_text})
        pipeline.attach(features_np, mask_np, adj)

        loader = DataLoader(
            Corpus(features_np, mask_np, adj),
            batch_size=8,
            collate_fn=make_completion_collate(list(features_np.keys())),
        )
        trainer = Completion(
            pipeline,
            Fit(),
            monitor=Monitor(),
            checkpoint_dir=tmp_path,
            device="cpu",
        )
        result = trainer.fit(loader, None, epochs=2, patience=4)
        assert "best" in result
        assert torch.isfinite(torch.tensor(result["best"])) or result["best"] == float("inf")

    def pipeline(self, tmp_path) -> None:
        """Half the items have their text modality masked."""
        rng = np.random.default_rng(1)
        n = 24
        features_np = {
            "visual": rng.normal(size=(n, 4)).astype(np.float32),
            "text": rng.normal(size=(n, 2)).astype(np.float32),
        }
        mask_np = np.ones((n, 2), dtype=np.float32)
        mask_np[n // 2 :, 1] = 0.0
        adj = build_path_graph(n)

        pipeline = Pipeline(Config(), dims={"visual": 4, "text": 2})
        pipeline.attach(features_np, mask_np, adj)

        features_t = {k: torch.from_numpy(v) for k, v in features_np.items()}
        mask_t = torch.from_numpy(mask_np)
        index = torch.arange(n)
        out = pipeline(features_t, mask_t, adj, index=index, training=False)
        assert out.completed["visual"].shape == (n, 4)
        assert out.completed["text"].shape == (n, 2)
        assert torch.isfinite(out.completed["text"]).all()

    def serving_score(self) -> None:
        """The serving score path uses attached corpus and completed features."""
        rng = np.random.default_rng(3)
        n = 12
        features = {
            "visual": rng.normal(size=(n, 4)).astype(np.float32),
            "text": rng.normal(size=(n, 2)).astype(np.float32),
        }
        mask = np.ones((n, 2), dtype=np.float32)
        item_graph = build_path_graph(n)
        ui = sp.csr_matrix(
            np.asarray(
                [[1 if (u + i) % 3 == 0 else 0 for i in range(n)] for u in range(4)],
                dtype=np.float32,
            )
        )
        pipeline = Pipeline(Config(), dims={"visual": 4, "text": 2})
        pipeline.attach(features, mask, item_graph)
        pipeline.wire(ui, feature_dim=6)
        scores = pipeline.score(torch.arange(4), torch.arange(n))
        cached = pipeline._score_cache
        assert cached is not None
        cached_features = cached[1]
        repeated = pipeline.score(torch.tensor([0]), torch.arange(n))
        assert pipeline._score_cache is not None
        assert pipeline._score_cache[1] is cached_features
        assert scores.shape == (4, n)
        assert repeated.shape == (1, n)
        assert torch.isfinite(scores).all()

    def serving_score_requires_state(self) -> None:
        """A pipeline without attached serving state fails explicitly."""
        pipeline = Pipeline(Config(), dims={"visual": 4, "text": 2})
        with pytest.raises(Model, match="no wired recommender"):
            pipeline.score(torch.zeros(1, dtype=torch.long), torch.zeros(1, dtype=torch.long))

    def rejects(self) -> None:
        """Pipeline raises Net when an adjacency with self-loops is passed."""
        rng = np.random.default_rng(2)
        n = 8
        features_np = {
            "visual": rng.normal(size=(n, 4)).astype(np.float32),
            "text": rng.normal(size=(n, 2)).astype(np.float32),
        }
        mask_np = np.ones((n, 2), dtype=np.float32)
        bad = sp.csr_matrix(np.eye(n, dtype=np.float32))
        pipeline = Pipeline(Config(), dims={"visual": 4, "text": 2})
        pipeline.attach(features_np, mask_np, bad)

        features_t = {k: torch.from_numpy(v) for k, v in features_np.items()}
        mask_t = torch.from_numpy(mask_np)
        with pytest.raises(Net):
            pipeline(features_t, mask_t, bad, training=False)
