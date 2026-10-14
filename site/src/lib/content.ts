export const SITE = {
  name: "morel",
  tagline: "Robust multimodal recommendation, one graph at a time.",
  description:
    "An open-source Python library for graph retrieval-enhanced modality completion. Build recommenders that finish missing modalities before ranking — paper-faithful, deterministic, and ready to validate.",
  repo: "https://github.com/sachncs/morel",
  repoName: "sachncs/morel",
  url: "https://sachncs.github.io/morel/",
  docs: "https://github.com/sachncs/morel/tree/master/docs",
  benchmarks: "https://github.com/sachncs/morel/blob/master/docs/reference/benchmarks.md",
  readiness: "https://github.com/sachncs/morel/blob/master/docs/reference/production-readiness.md",
  install: "pip install -e '.[dev,serve]'",
  python: "Python 3.10+",
  license: "MIT",
  version: "0.1",
  arxiv: "2605.00670",
} as const;

export const HERO_PILLS = [
  "Graph retrieval",
  "Modality completion",
  "Paper-faithful",
  "Serving foundation",
] as const;

// Updated only from a completed local audit; keep claims traceable to a
// dated verification run instead of silently presenting illustrative values.
export const VERIFICATION = {
  tests: 609,
  coverage: 84.57,
  lastVerified: "2026-10-13",
} as const;

export const PIPELINE_STAGES = [
  {
    title: "Bipartite interactions",
    body: "Stream user–item interactions into a CSR matrix. Bernoulli mask the modality slots you want to stress-test.",
    kbd: "morel data mask",
  },
  {
    title: "Anchor retrieval",
    body: "Per-modality cosine-NN anchors on the observed feature space. Optional BFS, ACS, or MAGE expansion over the item co-occurrence graph.",
    kbd: "morel.retrieve",
  },
  {
    title: "Modality completion",
    body: "Transformer encoder + VQ / Gumbel-VQ codebook reconstructs the missing modalities, with usage and load-balancing losses.",
    kbd: "morel.complete",
  },
  {
    title: "LightGCN ranking",
    body: "BPR-trained LightGCN ranker consumes the completed embeddings and serves top-K recommendations.",
    kbd: "morel.recommend",
  },
] as const;

export const FEATURES = [
  {
    title: "Modality completion",
    body:
      "VQ and Gumbel-VQ codebooks reconstruct missing modalities directly from graph context — no imputation hacks, no side features.",
    bullets: ["VQ · Gumbel-VQ", "Usage + balance losses", "Deterministic seeds"],
    icon: "codebook",
  },
  {
    title: "Graph retrieval",
    body:
      "BFS, anchor, ACS, and MAGE retrieval over the item co-occurrence graph. Pick the strategy that fits your latency budget.",
    bullets: ["Four strategies", "Per-modality top-K", "Budgeted expansion"],
    icon: "graph",
  },
  {
    title: "Paper-faithful",
    body:
      "Every algorithm ties to a paper equation. The build emits a machine-rendered fidelity report — every implementation choice is auditable.",
    bullets: ["FIDELITY.json", "Equation registry", "Regression tests"],
    icon: "shield",
  },
  {
    title: "Serving foundation",
    body:
      "FastAPI inference server with token auth, Prometheus metrics, and a cached model loader. Same code in dev and in prod.",
    bullets: ["FastAPI · Uvicorn", "Prometheus", "Docker · Compose"],
    icon: "bolt",
  },
  {
    title: "Reproducible by default",
    body:
      "Deterministic seeding, machine-rendered manifests, benchmark fixtures, and automated quality gates.",
    bullets: ["Seeded RNG", "Manifests per run", "CI benchmarks"],
    icon: "sparkles",
  },
  {
    title: "Composable config",
    body:
      "A frozen dataclass tree, overridable field by field. Defaults that match the paper; overrides that don't surprise you.",
    bullets: ["Frozen dataclasses", "YAML + env", "Strict types"],
    icon: "stack",
  },
] as const;

export const USE_CASES = [
  {
    industry: "E-commerce",
    title: "Finish the catalog before ranking.",
    body:
      "Long-tail SKUs rarely have clean visual or textual features. morel completes them from co-occurrence so the ranker never sees a hole.",
    metric: { label: "Sparse-catalog evaluation", value: "Measure" },
  },
  {
    industry: "Streaming & media",
    title: "Recommendations that don't break on cold assets.",
    body:
      "When a poster or synopsis is missing, the graph context fills it in. The LightGCN head ranks against a complete embedding.",
    metric: { label: "Cold-start evaluation", value: "Measure" },
  },
  {
    industry: "Marketplaces",
    title: "One pipeline, many modalities.",
    body:
      "Text, image, audio — morel treats them uniformly through per-modality anchors and a shared completion codebook.",
    metric: { label: "Modalities handled per pipeline", value: "Configurable" },
  },
] as const;

export const STATS = [
  { value: String(VERIFICATION.tests), label: "Tests passing" },
  { value: `${VERIFICATION.coverage.toFixed(2)}%`, label: "Code coverage" },
  { value: "4", label: "Retrieval strategies" },
  { value: "100", label: "Codebook entries" },
] as const;

export const FAQ = [
  {
    q: "Is morel a research project or a product?",
    a: "morel is an open-source Python library with research-grade fidelity. Every algorithm ties to a paper equation, and the codebase ships with a fidelity report, regression tests, and automated quality gates. The same code runs in notebooks and self-hosted deployments.",
  },
  {
    q: "Do I need a GPU?",
    a: "No. morel runs end-to-end on CPU for moderate corpora. For larger corpora or faster training, a CUDA-enabled PyTorch install unlocks GPU acceleration automatically; benchmark your own catalog before setting a capacity target.",
  },
  {
    q: "How does it compare to a vanilla LightGCN?",
    a: "morel layers graph retrieval and modality completion ahead of LightGCN. The repository includes benchmark fixtures so you can measure the effect on your own corpus; results depend on the graph, modalities, masking policy, and training configuration.",
  },
  {
    q: "What's the license?",
    a: "MIT. Use it in commercial products, modify it, ship it. Attribution is appreciated but not required.",
  },
  {
    q: "Can I bring my own modality encoder?",
    a: "Yes. morel exposes a thin encoder interface; swap in any model that returns an L2-normalized tensor. The default encoder wraps sentence-transformers and a torchvision backbone.",
  },
] as const;

export const ADOPTION = [
  {
    title: "Open source",
    price: "Free",
    description: "The full library, the demo, and the test suite. MIT licensed.",
    cta: "Get started",
    href: `${SITE.repo}#installation`,
    highlight: false,
    features: ["Full library", "All retrieval strategies", "All codebook variants", "Paper-fidelity report"],
  },
  {
    title: "Self-hosted",
    price: "Run it",
    description: "Docker Compose brings up the inference server with token auth and Prometheus metrics.",
    cta: "View Docker setup",
    href: `${SITE.repo}#option-3-docker-no-python-install-needed`,
    highlight: true,
    features: ["FastAPI inference", "Prometheus metrics", "Health-checked", "Token auth"],
  },
  {
    title: "Adopt & extend",
    price: "Your shape",
    description: "Plug morel's pipeline into your existing training stack. Public API, frozen config, strict typing.",
    cta: "Read the docs",
    href: `${SITE.repo}#where-to-go-next`,
    highlight: false,
    features: ["Public API surface", "Frozen config tree", "Strict typing", "mkdocstrings reference"],
  },
] as const;

export const TRUSTED_LOGOS = [
  "sentence-transformers",
  "PyTorch",
  "FastAPI",
  "Prometheus",
  "MkDocs",
  "Ruff",
  "mypy",
  "Docker",
] as const;

export const CODE_SAMPLE = `import torch
from morel import Config, Pipeline
from morel.data import bipartite, cooccurrence, bernoulli
from morel.recommend import Light

# 1. Build the bipartite user-item interaction graph.
ui = bipartite(users, items, interactions)

# 2. Build the item co-occurrence graph and a 40% modality mask.
adjacency = cooccurrence(ui)
mask = bernoulli(items, modalities=2, ratio=0.4, seed=42)

# 3. Attach your corpus and run the GRE-MC pipeline.
pipeline = Pipeline(Config.defaults(), dims={"visual": 16, "text": 8})
pipeline.attach(features, mask, adjacency)

output = pipeline(features, mask, adjacency, training=False)

# 4. Rank with the LightGCN-style head.
scores = Light(users=20, items=50, embed=32, layers=2)(
    torch.arange(20), torch.arange(50), ui
)
print(scores.shape)  # (20, 50)`;
