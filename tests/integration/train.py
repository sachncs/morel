"""Integration tests for the full pipeline."""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader

from morel.app.experiment import Experiment
from morel.core.config import Config
from morel.data.build import bipartite, cooccurrence
from morel.data.mask import bernoulli
from morel.pipeline import Pipeline
from morel.serve.factory import from_run
from morel.train.completion import Completion, Fit
from tests.shared import Corpus, build_path_graph, make_completion_collate


class Monitor:
    """Test monitor that discards metric logs."""

    def log(self, step: int | None = None, **metrics: object) -> None:
        """Discard the call and accept any keyword arguments."""
        return


class Checker:
    """Aggregated test methods for this module."""

    def end(self, tmp_path) -> None:
        rng = np.random.default_rng(0)
        users, items = 30, 50
        uids = rng.integers(0, users, size=300)
        iids = rng.integers(0, items, size=300)
        ui = bipartite(uids, iids, users, items)
        item_graph = cooccurrence(ui)

        features_np = {
            "visual": rng.normal(size=(items, 4)).astype(np.float32),
            "text": rng.normal(size=(items, 2)).astype(np.float32),
        }
        mask_np = bernoulli(items, 2, 0.4, seed=0).numpy()

        import torch

        config = Config()
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        pipeline.attach(features_np, mask_np, item_graph)

        features = {k: torch.from_numpy(v) for k, v in features_np.items()}
        mask = torch.from_numpy(mask_np)
        index = torch.arange(items)
        out = pipeline(features, mask, item_graph, index=index, training=False)
        assert out.completed["visual"].shape == (items, 4)
        assert out.completed["text"].shape == (items, 2)

    def trainer(self, tmp_path) -> None:
        rng = np.random.default_rng(0)
        n = 20
        features = {
            "visual": rng.normal(size=(n, 4)).astype(np.float32),
            "text": rng.normal(size=(n, 2)).astype(np.float32),
        }
        mask = np.ones((n, 2), dtype=np.float32)
        adj = build_path_graph(n)

        dataset = Corpus(features, mask, adj)
        loader = DataLoader(
            dataset,
            batch_size=4,
            collate_fn=make_completion_collate(list(features.keys())),
        )
        cfg = Fit()
        pipeline = Pipeline(Config(), dims={"visual": 4, "text": 2})
        pipeline.attach(features, mask, adj)
        trainer = Completion(pipeline, cfg, monitor=Monitor(), checkpoint_dir=tmp_path)
        trainer.fit(loader, loader, epochs=3, patience=5)

    def artifact_to_serving(self, tmp_path) -> None:
        """A real experiment artifact loads into the serving pipeline contract."""
        config = Config.parse(
            {
                "device": "cpu",
                "completion": {"epochs": 1, "batch": 8, "patience": 1},
            }
        )
        directory = tmp_path / "completion"
        report = Experiment(
            config,
            directory,
            items=8,
            users=4,
            dv=2,
            td=2,
            epochs=1,
            seed=0,
        ).run()
        pipeline = from_run(directory)
        scores = pipeline.score(torch.tensor([0]), torch.arange(8))
        assert report["cfg_hash"] == config.hash()
        assert pipeline.user_count == 4
        assert pipeline.item_count == 8
        assert scores.shape == (1, 8)
        assert torch.isfinite(scores).all()
