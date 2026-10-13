"""Tests for morel.pipeline."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp
import torch

from morel.core.config import Config
from morel.core.errors import Model
from morel.pipeline import Pipeline


class Checker:
    """Aggregated test methods for this module."""

    def end(self) -> None:
        config = Config.defaults()
        config = Config()
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        features = {
            "visual": torch.randn(3, 4),
            "text": torch.randn(3, 2),
        }
        mask = torch.tensor([[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]])
        adjacency = sp.csr_matrix(np.zeros((3, 3), dtype=np.float32))
        out = pipeline(features, mask, adjacency, training=False)
        assert out.completed["visual"].shape == (3, 4)
        assert out.completed["text"].shape == (3, 2)
        assert out.routing.shape == (3, config.codebook.size)

    def retrieval(self) -> None:
        config = Config()
        # Use a larger graph so PE has enough dimensions.
        n = 32
        rng = np.random.default_rng(0)
        features_np = {
            "visual": rng.normal(size=(n, 4)).astype(np.float32),
            "text": rng.normal(size=(n, 2)).astype(np.float32),
        }
        mask_np = np.ones((n, 2), dtype=np.float32)
        arr = np.zeros((n, n), dtype=np.float32)
        for i in range(n - 1):
            arr[i, i + 1] = 1
            arr[i + 1, i] = 1
        adjacency = sp.csr_matrix(arr)
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        pipeline.attach(features_np, mask_np, adjacency)
        index = torch.tensor([0, 1, 2])
        features = {k: torch.from_numpy(v[index.numpy()]) for k, v in features_np.items()}
        mask = torch.from_numpy(mask_np[index.numpy()])
        out = pipeline(features, mask, adjacency, index=index, training=False)
        assert out.completed["visual"].shape == (3, 4)
        assert out.subgraph_indices is not None
        assert out.subgraph_mask is not None

    def seed(self) -> None:
        """Two pipelines from one config must match despite differing ambient RNG."""
        config = Config()
        torch.manual_seed(1)
        first = Pipeline(config, dims={"visual": 4, "text": 2})
        torch.manual_seed(9999)
        second = Pipeline(config, dims={"visual": 4, "text": 2})

        left, right = first.state_dict(), second.state_dict()
        assert left.keys() == right.keys()
        for key in left:
            assert torch.equal(left[key], right[key]), f"parameter {key} differs"

    def state(self) -> None:
        config = Config()
        torch.manual_seed(7)
        expected = torch.randn(4)

        torch.manual_seed(7)
        Pipeline(config, dims={"visual": 4, "text": 2})
        actual = torch.randn(4)

        assert torch.equal(expected, actual)

    def instances(self) -> None:
        config = Config()
        features = {"visual": torch.randn(3, 4), "text": torch.randn(3, 2)}
        mask = torch.tensor([[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]])
        adjacency = sp.csr_matrix(np.zeros((3, 3), dtype=np.float32))

        first = Pipeline(config, dims={"visual": 4, "text": 2})(
            features, mask, adjacency, training=False
        )
        second = Pipeline(config, dims={"visual": 4, "text": 2})(
            features, mask, adjacency, training=False
        )

        assert torch.equal(first.routing, second.routing)
        for name in first.completed:
            assert torch.equal(first.completed[name], second.completed[name])

    def dropout(self) -> None:
        """Regression: training=False left nn.Dropout active, so inference was noisy."""
        config = Config()
        assert config.encode.dropout > 0, "test needs a nonzero dropout to be meaningful"
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        features = {"visual": torch.randn(3, 4), "text": torch.randn(3, 2)}
        mask = torch.ones(3, 2)
        adjacency = sp.csr_matrix(np.zeros((3, 3), dtype=np.float32))

        first = pipeline(features, mask, adjacency, training=False)
        second = pipeline(features, mask, adjacency, training=False)

        assert torch.equal(first.routing, second.routing)
        for name in first.completed:
            assert torch.equal(first.completed[name], second.completed[name])

    def mode(self) -> None:
        config = Config()
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        features = {"visual": torch.randn(3, 4), "text": torch.randn(3, 2)}
        mask = torch.ones(3, 2)
        adjacency = sp.csr_matrix(np.zeros((3, 3), dtype=np.float32))

        assert pipeline.training is True
        pipeline(features, mask, adjacency, training=False)
        assert pipeline.training is True, "an inference pass must not leave the module in eval mode"

        pipeline.eval()
        pipeline(features, mask, adjacency, training=True)
        assert pipeline.training is False, "a training pass must not leave the module in train mode"

    def cache(self) -> None:
        """Regression: wire used to raise AttributeError."""
        config = Config()
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        ui = sp.csr_matrix(np.array([[1, 0, 1], [0, 1, 1]], dtype=np.float32))

        pipeline.wire(ui)

        assert pipeline.recommender is not None
        assert pipeline.recommender.users == 2
        assert pipeline.recommender.items == 3
        assert pipeline.recommender.cache is not None

    def warmup(self) -> None:
        """Serving warm-up materializes graph state before the first request."""
        config = Config()
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        adjacency = sp.csr_matrix(np.array([[0, 1], [1, 0]], dtype=np.float32))
        features = {
            "visual": np.ones((2, 4), dtype=np.float32),
            "text": np.ones((2, 2), dtype=np.float32),
        }
        pipeline.attach(features, np.ones((2, 2), dtype=np.float32), adjacency)
        pipeline.warmup()
        assert len(pipeline.encoder.cache) == 1

        pipeline.cadj = None
        with pytest.raises(Model, match="attached item graph"):
            pipeline.warmup()

    def prepared_graph_cache(self) -> None:
        """A normalized ranker receives no graph after Pipeline.wire prepares it."""
        from unittest.mock import patch

        from morel.recommend.light import key

        config = Config()
        pipeline = Pipeline(config, dims={"visual": 4, "text": 2})
        features = {
            "visual": np.ones((3, 4), dtype=np.float32),
            "text": np.ones((3, 2), dtype=np.float32),
        }
        item_graph = sp.csr_matrix(np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.float32))
        ui_graph = sp.csr_matrix(np.array([[1, 0, 1], [0, 1, 1]], dtype=np.float32))
        pipeline.attach(features, np.ones((3, 2), dtype=np.float32), item_graph)
        pipeline.wire(ui_graph, feature_dim=6)
        assert pipeline.recommender is not None
        with patch("morel.recommend.light.key", wraps=key) as fingerprint:
            pipeline.score(torch.tensor([0]), torch.tensor([0]))
            pipeline.score(torch.tensor([0]), torch.tensor([0]))
        assert fingerprint.call_count == 0

    def attach_snapshot(self) -> None:
        """Attached corpus data is validated and isolated from caller mutation."""
        config = Config()
        pipeline = Pipeline(config, dims={"visual": 3, "text": 2})
        features = {
            "visual": np.ones((4, 3), dtype=np.float64),
            "text": np.ones((4, 2), dtype=np.float64),
        }
        mask = np.ones((4, 2), dtype=np.float64)
        adjacency = sp.eye(4, format="csr", dtype=np.float32)
        pipeline.attach(features, mask, adjacency)

        features["visual"][0, 0] = 99
        mask[0, 0] = 0
        adjacency.data[:] = 0
        assert pipeline.cfeat is not features
        assert pipeline.cfeat["visual"][0, 0] == 1
        assert pipeline.cmask[0, 0] == 1
        assert pipeline.cadj.nnz == 4

        with pytest.raises(ValueError, match="modalities mismatch"):
            pipeline.attach({"visual": np.ones((4, 3))}, mask, adjacency)
        with pytest.raises(ValueError, match="adjacency must have shape"):
            pipeline.attach(features, mask, sp.eye(3, format="csr"))

    def config(self) -> None:
        config = Config()
        ui = sp.csr_matrix(np.array([[1, 0, 1], [0, 1, 1]], dtype=np.float32))

        first = Pipeline(config, dims={"visual": 4, "text": 2})
        torch.manual_seed(1)
        first.wire(ui)
        second = Pipeline(config, dims={"visual": 4, "text": 2})
        torch.manual_seed(4321)
        second.wire(ui)

        assert first.recommender is not None
        assert second.recommender is not None
        assert torch.equal(first.recommender.user_emb.weight, second.recommender.user_emb.weight)
