"""End-to-end determinism contract.

Regression coverage for the case that motivated the seeding work: running the
same configured pipeline twice in one process used to produce different
metrics, because model parameters were drawn from the ambient global RNG and
dropout stayed active during inference.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import torch

from morel.core.config import Config
from morel.data.build import bipartite, cooccurrence
from morel.data.mask import bernoulli
from morel.eval import ndcg, recall
from morel.pipeline import Pipeline
from morel.recommend import Light


def synthetic() -> tuple[dict[str, np.ndarray], np.ndarray, sp.csr_matrix, sp.csr_matrix]:
    """Build the small synthetic user-item problem used by the demo."""
    rng = np.random.default_rng(0)
    users, items = 20, 50
    ui = bipartite(rng.integers(0, users, size=200), rng.integers(0, items, size=200), users, items)
    features = {
        "visual": rng.normal(size=(items, 16)).astype(np.float32),
        "text": rng.normal(size=(items, 8)).astype(np.float32),
    }
    mask = bernoulli(items, 2, 0.4, seed=42).numpy()
    return features, mask, cooccurrence(ui), ui


def run(config: Config) -> tuple[dict[str, torch.Tensor], torch.Tensor, float, float]:
    """Run the demo flow end to end and return its outputs and metrics."""
    features, mask, adjacency, ui = synthetic()
    items = mask.shape[0]
    users = ui.shape[0]

    pipeline = Pipeline(config, dims={"visual": 16, "text": 8})
    pipeline.attach(features, mask, adjacency)
    output = pipeline(
        {name: torch.from_numpy(value) for name, value in features.items()},
        torch.from_numpy(mask),
        adjacency,
        index=torch.arange(items),
        training=False,
    )

    recommender = Light(users=users, items=items, embed=32, layers=2, seed=config.seed)
    scores = recommender(torch.arange(users), torch.arange(items), ui).detach().numpy()
    labels = ui.sign().toarray()
    return (
        output.completed,
        output.routing,
        float(recall(scores, labels, k=10)),
        float(ndcg(scores, labels, k=10)),
    )


class Checker:
    """Aggregated test methods for this module."""

    def same(self) -> None:
        config = Config()
        torch.manual_seed(1)
        _, _, recall_a, ndcg_a = run(config)
        torch.manual_seed(9999)
        _, _, recall_b, ndcg_b = run(config)

        assert recall_a == recall_b
        assert ndcg_a == ndcg_b

    def config(self) -> None:
        config = Config()
        torch.manual_seed(1)
        completed_a, routing_a, _, _ = run(config)
        torch.manual_seed(9999)
        completed_b, routing_b, _, _ = run(config)

        assert torch.equal(routing_a, routing_b)
        assert completed_a.keys() == completed_b.keys()
        for name in completed_a:
            assert torch.equal(completed_a[name], completed_b[name]), f"modality {name} differs"

    def different(self) -> None:
        """Determinism must come from the seed, not from the model being constant."""
        _, routing_a, _, _ = run(Config())
        _, routing_b, _, _ = run(Config(seed=7))

        assert not torch.equal(routing_a, routing_b)

    def process(self, tmp_path) -> None:
        """``python examples/demo.py`` must be byte-identical across two processes."""
        import os
        import subprocess
        import sys
        from pathlib import Path

        repo = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = "0"
        env["PYTHONPATH"] = str(repo)
        runs = []
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, "examples/demo.py"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            runs.append(result.stdout)
        assert runs[0] == runs[1], "demo output drifted between two processes"

    def graph(self) -> None:
        """Cooccurrence on 20k users / 5k items fits in well under 5s and 1GB."""
        import resource
        import time

        import numpy as np
        from scipy.sparse import csr_matrix

        from morel.data.build import cooccurrence, kcore

        rng = np.random.default_rng(0)
        users, items = 20_000, 5_000
        ui = csr_matrix(
            (
                np.ones(200_000, dtype=np.float32),
                (rng.integers(0, users, size=200_000), rng.integers(0, items, size=200_000)),
            ),
            shape=(users, items),
        )
        t0 = time.perf_counter()
        cooc = cooccurrence(ui)
        _ = kcore(cooc, min_edges=3)
        elapsed = time.perf_counter() - t0
        # ru_maxrss is in bytes on macOS, kilobytes on Linux. Normalize.
        raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mb = raw_rss / (1024 * 1024) if raw_rss > 10_000_000 else raw_rss / 1024
        assert elapsed < 5.0, f"cooccurrence+kcore took {elapsed:.2f}s"
        assert rss_mb < 1024, f"peak RSS {rss_mb:.0f}MB exceeds 1GB budget"
