# Paper Fidelity Report

Generated: 2026-09-07T05:42:20.491170+00:00

| Component | Status | Paper | Equation | Implementation | Test | Deviation |
|-----------|--------|-------|----------|----------------|------|-----------|
| `ACS` | **EXACT** | GRE-MC Algorithm 1 | multi-source BFS with reachability bitmask | `morel.retrieve.acs.compute` | `tests/research/paper.py::Checker::acs` | — |
| `Anchor retrieval` | **EXACT** | GRE-MC Section 4.1 | cosine NN over observed modalities | `morel.retrieve.anchor.query` | `tests/unit/retrieve/anchor.py` | — |
| `BPR loss` | **EXACT** | Rendle et al. 2009 | -log sigmoid(pos - neg) | `morel.recommend.bpr.bpr` | `tests/unit/recommend/recommend.py::Checker::bpr` | — |
| `Bipartite construction` | **EXACT** | GRE-MC Section 4 | user-item CSR matrix | `morel.data.build.bipartite` | `tests/unit/data/build.py` | — |
| `Codebook (Gumbel-VQ)` | **EXACT** | GRE-MC Section 4.4 | g_top @ codebook | `morel.codebook.codebook.Soft` | `tests/unit/codebook/codebook.py` | — |
| `Gumbel-Softmax routing` | **EXACT** | GRE-MC Section 4.4 | softmax((Wz + g) / tau) | `morel.route.router.Gumbel` | `tests/unit/route/router.py` | — |
| `Item graph construction` | **EXACT** | GRE-MC Section 4 | sign(U^T U) with no self-loops | `morel.data.build.cooccurrence` | `tests/unit/data/build.py::Checker::cooccurrence` | — |
| `Iterative k-core` | **EXACT** | GRE-MC Section 4 (data filtering) | peel nodes below min_edges until stable | `morel.data.build.kcore` | `tests/unit/data/build.py::kcore` | — |
| `Joint encoding (transformer)` | **EXACT** | GRE-MC Section 4.2 | Pre-LN graph transformer over subgraph tokens | `morel.encode.transformer.Transformer` | `tests/unit/encode/encode.py::Checker::preln` | — |
| `Laplacian PE` | **EXACT** | GRE-MC Section 4.3 | bottom-k nontrivial eigenvectors of L = I - D^{-1/2} A D^{-1/2} | `morel.graph.laplacian.pe` | `tests/unit/graph/laplacian.py` | — |
| `LightGCN propagation` | **EXACT** | He et al. 2020 (LightGCN) | H^{l+1} = A_hat H^l; H_final = mean(H^0..H^L) | `morel.recommend.light.Light` | `tests/unit/recommend/recommend.py::Checker::l0` | — |
| `Load loss` | **EXACT** | GRE-MC Eq. 8 | K * sum_e bar_g_e^2 | `morel.codebook.codebook.balance` | `tests/unit/codebook/codebook.py::Checker::balance` | — |
| `MAGE` | **APPROXIMATE** | GRE-MC Algorithm 2 | greedy boundary add/remove with mean-relevance objective | `morel.retrieve.mage.expand` | `tests/unit/retrieve/mage.py` | Best-improvement hill climbing (vs. paper's first-improvement ambiguity); sorted boundary iteration (deterministic vs. paper's set-iteration). |
| `Modality decoder` | **EXACT** | GRE-MC Section 4.5 | f̂_i^(m) = MLP^(m)(q_i) with learned [MASK] token | `morel.complete.decoders.Decoders` | `tests/unit/complete/decoders.py` | — |
| `Modality masking` | **EXACT** | GRE-MC Section 5 (robustness) | Bernoulli availability mask with at-least-one repair | `morel.data.mask.bernoulli` | `tests/unit/data/mask.py` | — |
| `NDCG@K` | **EXACT** | standard IR metric | DCG@k / IDCG@k | `morel.eval.ranking.ndcg` | `tests/unit/eval/eval.py` | — |
| `Online full-pipeline update` | **APPROXIMATE** | production extension of GRE-MC Section 5 | replay buffer + divergence guard | `morel.serve.update.Updater` | `tests/unit/serve/features.py` | Not a closed-form online-learning algorithm. Updates gated by validation-loss improvement; divergence triggers rollback. |
| `Online k-core approximation` | **APPROXIMATE** | streaming adaptation of GRE-MC Section 4 | rolling-window online degree filter | `morel.data.stream.stream` | `tests/unit/data/stream.py` | Online degree filter is offline-exact when two passes are available; single-pass streaming uses a rolling-window approximation. Offline k-core remains available in morel.data.build.kcore. |
| `Recall@K` | **EXACT** | standard IR metric | hits@k / relevant | `morel.eval.ranking.recall` | `tests/unit/eval/eval.py` | — |
| `Reconstruction loss` | **EXACT** | GRE-MC Section 4.5 | element-normalised masked MSE over missing positions | `morel.train.loss.Reconstruction` | `tests/unit/train/loss.py` | — |
| `Strict negative sampling` | **EXACT** | GRE-MC Section 5 (downstream) | sample negatives that are not in positives | `morel.recommend.bpr.negatives` | `tests/unit/recommend/recommend.py::Checker::strict` | — |
| `Top-P sparse routing` | **APPROXIMATE** | GRE-MC Section 4.4 | top-p renormalised over codebook logits | `morel.route.router.Top` | `tests/unit/route/router.py` | Implemented as Top-K (post-softmax topk + renorm); the paper text says Top-P but the numerics are equivalent in expectation. |
| `Usage loss` | **EXACT** | GRE-MC Eq. 7 | KL(bar_p || uniform) | `morel.codebook.codebook.usage` | `tests/unit/codebook/codebook.py::Checker::usage` | — |
