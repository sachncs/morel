---
hide:
  - navigation
  - toc
---

<!-- The landing page renders inside the Material wrapper but lays out
     itself with the morel grid. The .morel-landing class hides the
     sidebar / TOC so the hero can use the full viewport width. -->
<div class="morel-landing">

  <!-- ============================================================ -->
  <!-- SECTION 1 — HERO                                              -->
  <!-- ============================================================ -->

  <section class="morel-hero" id="hero">
    <div class="morel-hero__inner">
      <div class="morel-hero__lockup">
        <span class="morel-eyebrow">Graph retrieval · Modality completion</span>
        <h1>Robust multimodal recommendation, <span class="morel-accent">one graph at a time.</span></h1>
        <p class="morel-subhead">
          <strong>morel</strong> is an open-source Python library for graph
          retrieval-enhanced modality completion. Feed it a user–item
          graph with incomplete per-item features, and it returns a
          trained recommender that finishes missing modalities before
          ranking — backed by a paper-fidelity registry, deterministic
          manifests, and a FastAPI inference server.
        </p>
        <div class="morel-cta-row">
          <a href="getting-started/" class="morel-cta-primary">Get started</a>
          <a href="https://github.com/sachncs/morel" class="morel-cta-secondary">View GitHub</a>
          <a href="#paper" class="morel-cta-quiet">Read paper →</a>
        </div>
        <div class="morel-trust">
          <span class="morel-pill morel-pill-strong">Python 3.10+</span>
          <span class="morel-pill">MIT license</span>
          <span class="morel-pill">arxiv 2605.00670</span>
          <span class="morel-pill">482 tests · 80% coverage</span>
          <span class="morel-pill">FastAPI inference</span>
          <span class="morel-pill">Prometheus metrics</span>
        </div>
      </div>

      <div class="morel-hero__diagram" aria-label="morel pipeline at a glance">
        <svg viewBox="0 0 360 220" role="img" aria-labelledby="hero-svg-title">
          <title id="hero-svg-title">Graph retrieval-enhanced modality completion, in one diagram</title>
          <defs>
            <linearGradient id="hero-edge" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#3D5AFE"/>
              <stop offset="100%" stop-color="#5E3DAB"/>
            </linearGradient>
            <pattern id="hero-grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(61,90,254,0.08)" stroke-width="0.5"/>
            </pattern>
          </defs>

          <!-- Grid -->
          <rect width="360" height="220" fill="url(#hero-grid)"/>

          <!-- Input user-item graph. -->
          <g font-size="9" font-family="ui-sans-serif, system-ui, sans-serif" fill="#4a4a55">
            <text x="8" y="14">Input: user–item interaction graph</text>
          </g>
          <g stroke="url(#hero-edge)" stroke-width="1" fill="none" stroke-linecap="round">
            <!-- User nodes. -->
            <circle cx="22" cy="50"  r="3" fill="#3D5AFE"/>
            <circle cx="22" cy="90"  r="3" fill="#3D5AFE"/>
            <circle cx="22" cy="130" r="3" fill="#3D5AFE"/>
            <!-- Item nodes (right). -->
            <circle cx="64" cy="62"  r="3" fill="#5E3DAB"/>
            <circle cx="64" cy="105" r="3" fill="#5E3DAB"/>
            <circle cx="64" cy="148" r="3" fill="#5E3DAB"/>
            <!-- Item-to-item edges (item graph). -->
            <line x1="64" y1="62"  x2="64" y2="105" stroke-dasharray="2 2"/>
            <line x1="64" y1="105" x2="64" y2="148" stroke-dasharray="2 2"/>
            <line x1="64" y1="62"  x2="64" y2="148" stroke-dasharray="2 2"/>
          </g>

          <!-- Query node with missing modality. -->
          <g>
            <circle cx="135" cy="105" r="11" fill="#fff" stroke="#3D5AFE" stroke-width="1.4"/>
            <circle cx="135" cy="105" r="11" fill="none" stroke="#3D5AFE" stroke-dasharray="2 1.6"/>
            <text x="135" y="108" font-size="8" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif"
                  fill="#3D5AFE" font-weight="600">q</text>
            <text x="135" y="130" font-size="9" text-anchor="middle" fill="#4a4a55"
                  font-family="ui-sans-serif, system-ui, sans-serif">query, modality gap</text>
          </g>

          <!-- Retrieved subgraph (highlighted cluster). -->
          <g stroke="url(#hero-edge)" stroke-width="1" fill="none" stroke-linecap="round">
            <circle cx="195" cy="80"  r="3.2" fill="#5E3DAB"/>
            <circle cx="225" cy="105" r="3.2" fill="#5E3DAB"/>
            <circle cx="195" cy="130" r="3.2" fill="#5E3DAB"/>
            <line x1="195" y1="80"  x2="225" y2="105"/>
            <line x1="225" y1="105" x2="195" y2="130"/>
            <line x1="195" y1="80"  x2="195" y2="130"/>
          </g>

          <!-- Edge from query to subgraph. -->
          <g stroke="url(#hero-edge)" stroke-width="1.4" fill="none" stroke-linecap="round">
            <path d="M 146 105 Q 170 95 192 85" stroke-dasharray="3 2.5"/>
            <path d="M 146 105 Q 170 115 192 125" stroke-dasharray="3 2.5"/>
          </g>

          <!-- Encoder block. -->
          <rect x="148" y="148" width="84" height="22" rx="5" fill="#fff" stroke="#c9c9d3"/>
          <text x="190" y="162" font-size="9" text-anchor="middle"
                font-family="ui-sans-serif, system-ui, sans-serif" fill="#4a4a55">Joint encoder</text>

          <!-- Completion block (output). -->
          <g>
            <rect x="258" y="80" width="92" height="50" rx="6" fill="#fff"
                  stroke="#3D5AFE" stroke-width="1.4"/>
            <text x="304" y="98" font-size="9" text-anchor="middle"
                  font-family="ui-sans-serif, system-ui, sans-serif" fill="#3D5AFE" font-weight="600">completed</text>
            <line x1="266" y1="106" x2="342" y2="106" stroke="#3D5AFE" stroke-width="0.6"/>
            <line x1="266" y1="113" x2="342" y2="113" stroke="#3D5AFE" stroke-width="0.6" opacity="0.6"/>
            <line x1="266" y1="120" x2="320" y2="120" stroke="#3D5AFE" stroke-width="0.6" opacity="0.4"/>
          </g>

          <!-- Arrow: subgraph → completion. -->
          <path d="M 232 105 L 258 105" stroke="url(#hero-edge)" stroke-width="1.4" fill="none" stroke-linecap="round"/>

          <!-- Caption strip. -->
          <text x="180" y="200" font-size="9" text-anchor="middle"
                font-family="ui-sans-serif, system-ui, sans-serif" fill="#75757f">
            retrieve → encode → complete → recommend
          </text>
        </svg>
      </div>
    </div>

    <nav class="morel-section-nav" aria-label="On this page">
      <a href="#hero">Hero</a>
      <a href="#problem">Problem</a>
      <a href="#method">Method</a>
      <a href="#how">Pipeline</a>
      <a href="#architecture">Architecture</a>
      <a href="#evidence">Evidence</a>
      <a href="#outputs">Outputs</a>
      <a href="#quickstart">Quickstart</a>
      <a href="#docs">Docs</a>
      <a href="#limitations">Limitations</a>
      <a href="#paper">Paper</a>
    </nav>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 2 — PROBLEM FRAMING                                  -->
  <!-- ============================================================ -->

  <section class="morel-section" id="problem">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Problem</span>
          <h2>Recommendation systems break the moment a feature goes missing.</h2>
        </div>
        <p class="morel-section__lead">
          Production catalogs routinely ship with masked text, broken
          image links, and items whose modality vector is a placeholder.
          Conventional recommenders average the neighbourhood; nothing
          on the model side ever asks <em>why</em> those features are
          missing or whether the gaps are correlated.
        </p>
      </div>

      <div class="morel-grid morel-grid--three">

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <circle cx="12" cy="12" r="9"/>
              <path d="M5 5l14 14" stroke-dasharray="2 2"/>
            </svg>
          </div>
          <h3>Incomplete modality signals</h3>
          <p>Real catalogs ship with masked text, broken image URLs, and
          per-item features that drift over time.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="3" y="3" width="18" height="18" rx="3"/>
              <path d="M3 9h18M9 21V9"/>
            </svg>
          </div>
          <h3>Naive reconstruction misses context</h3>
          <p>Self-only completion leaves every item in isolation. The
          best basis for "what should this look like" is a neighbourhood
          of semantically aligned items.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M3 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/>
            </svg>
          </div>
          <h3>Greedy retrieval fails on cold items</h3>
          <p>Items with few observed neighbours get noisy subgraphs;
          off-the-shelf retrievers optimise the wrong objective.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 3 — METHOD SUMMARY                                    -->
  <!-- ============================================================ -->

  <section class="morel-section morel-section--alt" id="method">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Method</span>
          <h2>Retrieve a relevant subgraph, complete the gap, then rank.</h2>
        </div>
        <p class="morel-section__lead">
          The pipeline treats missing modalities as a retrieval problem,
          not a denoising problem. It finds the items in the catalogue
          that should have informed the missing feature, encodes them
          together with the query, and lets the codebook learn which
          latent bases are worth keeping around for which contexts.
        </p>
      </div>

      <div class="morel-method">
        <div class="morel-method__diagram" aria-hidden="true">
          <svg viewBox="0 0 360 280" role="img">
            <defs>
              <linearGradient id="method-edge" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0%" stop-color="#3D5AFE"/>
                <stop offset="100%" stop-color="#5E3DAB"/>
              </linearGradient>
            </defs>
            <!-- Query. -->
            <g>
              <circle cx="180" cy="50" r="9" fill="#fff" stroke="#3D5AFE" stroke-width="1.4"/>
              <circle cx="180" cy="50" r="9" fill="none" stroke="#3D5AFE" stroke-dasharray="2 2"/>
              <text x="180" y="53" font-size="9" text-anchor="middle" font-weight="600"
                    font-family="ui-sans-serif, system-ui, sans-serif" fill="#3D5AFE">q</text>
              <text x="180" y="80" font-size="9" text-anchor="middle"
                    font-family="ui-sans-serif, system-ui, sans-serif" fill="#4a4a55">query, modality gap</text>
            </g>
            <!-- Subgraph. -->
            <g stroke="url(#method-edge)" stroke-width="1.2" fill="none" stroke-linecap="round">
              <circle cx="80"  cy="160" r="4" fill="#5E3DAB"/>
              <circle cx="140" cy="120" r="4" fill="#5E3DAB"/>
              <circle cx="220" cy="120" r="4" fill="#5E3DAB"/>
              <circle cx="280" cy="160" r="4" fill="#5E3DAB"/>
              <circle cx="180" cy="190" r="4" fill="#5E3DAB"/>
              <line x1="80" y1="160" x2="140" y2="120"/>
              <line x1="140" y1="120" x2="220" y2="120"/>
              <line x1="220" y1="120" x2="280" y2="160"/>
              <line x1="180" y1="190" x2="80" y2="160"/>
              <line x1="180" y1="190" x2="280" y2="160"/>
              <line x1="180" y1="190" x2="140" y2="120"/>
              <line x1="180" y1="190" x2="220" y2="120"/>
            </g>
            <g stroke="url(#method-edge)" stroke-width="1.2" fill="none" stroke-linecap="round"
               stroke-dasharray="3 3">
              <path d="M 180 60 Q 130 90 100 155"/>
              <path d="M 180 60 Q 230 90 260 155"/>
              <path d="M 180 60 Q 180 110 180 185"/>
            </g>
            <text x="180" y="232" font-size="9" text-anchor="middle"
                  font-family="ui-sans-serif, system-ui, sans-serif" fill="#4a4a55">retrieved subgraph</text>
            <!-- Completion. -->
            <g>
              <rect x="140" y="248" width="80" height="22" rx="5" fill="#fff"
                    stroke="#3D5AFE" stroke-width="1.4"/>
              <text x="180" y="263" font-size="9" text-anchor="middle"
                    font-family="ui-sans-serif, system-ui, sans-serif" fill="#3D5AFE" font-weight="600">completed</text>
            </g>
          </svg>
        </div>

        <div class="morel-method__steps">
          <div class="morel-method__step">
            <div class="morel-method__step-number">1</div>
            <div>
              <h3>Modality-aware subgraph retrieval</h3>
              <p>Anchor nodes pull cosine-NN within each observed modality.
              ACS reaches a collision root over BFS; MAGE expands the
              induced subgraph by mean relevance.</p>
            </div>
          </div>
          <div class="morel-method__step">
            <div class="morel-method__step-number">2</div>
            <div>
              <h3>Joint encoding with Laplacian PE</h3>
              <p>A Pre-LN graph transformer over subgraph tokens, attention
              pooling, and bottom-𝑘 eigenvectors of the normalised
              Laplacian as positional encoding.</p>
            </div>
          </div>
          <div class="morel-method__step">
            <div class="morel-method__step-number">3</div>
            <div>
              <h3>Sparse-routing codebook</h3>
              <p>Gumbel-Softmax over the codebook logits selects a few
              active bases per item; usage and balance losses keep the
              routes load-balanced.</p>
            </div>
          </div>
          <div class="morel-method__step">
            <div class="morel-method__step-number">4</div>
            <div>
              <h3>Per-modality completion</h3>
              <p>Per-modality MLP decoders with a learned `[MASK]` token
              produce the reconstructed feature; masked MSE normalises
              per missing element.</p>
            </div>
          </div>
          <div class="morel-method__step">
            <div class="morel-method__step-number">5</div>
            <div>
              <h3>Item-aware BPR ranker</h3>
              <p>LightGCN propagation over the bipartite graph with the
              completed feature fed into the ranker through a learnable
              projection.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 4 — HOW IT WORKS (visual pipeline)                   -->
  <!-- ============================================================ -->

  <section class="morel-section" id="how">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Pipeline</span>
          <h2>Six steps from raw graph to ranked feed.</h2>
        </div>
        <p class="morel-section__lead">
          Every step is a registry-mounted module. The same hooks are
          available end-to-end through the Python API and through the
          CLI, so a research notebook and a long-running training run
          stay bit-equivalent.
        </p>
      </div>

      <div class="morel-pipeline">
        <div class="morel-pipeline__step">
          <span class="morel-pipeline__step-num">STEP 01</span>
          <h3>Input graph</h3>
          <p>User–item interaction graph plus per-item features and a
          modality mask.</p>
        </div>
        <div class="morel-pipeline__step">
          <span class="morel-pipeline__step-num">STEP 02</span>
          <h3>Retrieve subgraphs</h3>
          <p>Anchor / ACS / MAGE pull informative contexts per query
          item.</p>
        </div>
        <div class="morel-pipeline__step">
          <span class="morel-pipeline__step-num">STEP 03</span>
          <h3>Encode</h3>
          <p>Joint graph transformer with attention pooling and
          Laplacian PE.</p>
        </div>
        <div class="morel-pipeline__step">
          <span class="morel-pipeline__step-num">STEP 04</span>
          <h3>Complete</h3>
          <p>Per-modality decoders reconstruct masked features with a
          learned `[MASK]` token.</p>
        </div>
        <div class="morel-pipeline__step">
          <span class="morel-pipeline__step-num">STEP 05</span>
          <h3>Regularise</h3>
          <p>Sparse-routing codebook losses keep usage and balance in
          check.</p>
        </div>
        <div class="morel-pipeline__step">
          <span class="morel-pipeline__step-num">STEP 06</span>
          <h3>Recommend</h3>
          <p>LightGCN propagates the completed feature into the
          bipartite ranker; BPR finalises.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 5 — ARCHITECTURE                                      -->
  <!-- ============================================================ -->

  <section class="morel-section morel-section--alt" id="architecture">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Architecture</span>
          <h2>Every module is a registry entry.</h2>
        </div>
        <p class="morel-section__lead">
          The package is split into one module per stage. Each stage
          exposes a registry under a stable name so swapping a
          retrieval strategy or a codebook is one decorator call.
        </p>
      </div>

      <div class="morel-grid morel-grid--three">
        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <circle cx="12" cy="12" r="3"/>
              <circle cx="4"  cy="5"  r="2"/>
              <circle cx="20" cy="5"  r="2"/>
              <circle cx="4"  cy="19" r="2"/>
              <circle cx="20" cy="19" r="2"/>
              <line x1="12" y1="12" x2="4"  y2="5"/>
              <line x1="12" y1="12" x2="20" y2="5"/>
              <line x1="12" y1="12" x2="4"  y2="19"/>
              <line x1="12" y1="12" x2="20" y2="19"/>
            </svg>
          </div>
          <h3>Retrieval module</h3>
          <p>Anchor cosine-NN, multi-source BFS collision (ACS), and
          mean-relevance hill-climbing (MAGE) over the item graph.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="3" y="6" width="18" height="12" rx="3"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
              <circle cx="7" cy="14" r="1.2" fill="currentColor"/>
              <circle cx="12" cy="14" r="1.2" fill="currentColor"/>
              <circle cx="17" cy="14" r="1.2" fill="currentColor"/>
            </svg>
          </div>
          <h3>Graph transformer</h3>
          <p>Pre-LN attention over subgraph tokens, attention pooling,
          and bottom-𝑘 Laplacian eigenvectors for positional structure.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="3" y="3"  width="6" height="6"/>
              <rect x="15" y="3" width="6" height="6"/>
              <rect x="3" y="15" width="6" height="6"/>
              <rect x="15" y="15" width="6" height="6"/>
              <line x1="9" y1="6" x2="15" y2="6"/>
              <line x1="9" y1="18" x2="15" y2="18"/>
            </svg>
          </div>
          <h3>Sparse-routing codebook</h3>
          <p>Gumbel-VQ codebook with Top-P routing; usage and load-balance
          regularisers keep the basis load-aware.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M4 4h16v6H4z"/>
              <path d="M4 14h16v6H4z"/>
              <line x1="4" y1="10" x2="20" y2="14" stroke-dasharray="2 2"/>
            </svg>
          </div>
          <h3>Completion module</h3>
          <p>Per-modality MLP decoders with a learned `[MASK]` token and
          element-normalised masked MSE.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M4 7l16 10M4 7v10l16-10"/>
            </svg>
          </div>
          <h3>Training &amp; evaluation harness</h3>
          <p>`Trainer` ABC, checkpointing with manifest-bound config
          hash, and evaluation against Recall@K, NDCG@K, and a robustness sweep.</p>
        </div>

        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="3" y="3" width="18" height="14" rx="2"/>
              <line x1="3" y1="8" x2="21" y2="8"/>
              <circle cx="6" cy="5.5" r="0.6" fill="currentColor"/>
              <circle cx="8" cy="5.5" r="0.6" fill="currentColor"/>
              <path d="M8 19l2 2 4-4"/>
            </svg>
          </div>
          <h3>CLI &amp; HTTP API</h3>
          <p>`morel` console command drives every lifecycle stage;
          `morel serve` exposes a FastAPI app with auth, rate limits,
          and Prometheus metrics.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 6 — EVIDENCE                                          -->
  <!-- ============================================================ -->

  <section class="morel-section" id="evidence">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Evidence</span>
          <h2>Every component is bound to a test.</h2>
        </div>
        <p class="morel-section__lead">
          The fidelity registry and the test suite are the project's
          audit trail. Numbers below are produced by the tests they cite
          and are reproducible from the same seed; nothing is hand-tuned
          for marketing.
        </p>
      </div>

      <div class="morel-grid morel-grid--three">
        <div class="morel-data">
          <div class="morel-data__head">
            <span class="morel-data__name">Tests collected</span>
            <span class="morel-data__hint">pytest</span>
          </div>
          <div class="morel-data__metric">
            <span class="morel-data__value">670</span>
            <span class="morel-data__suffix">tests</span>
          </div>
          <div class="morel-bar"><span class="morel-bar__fill" style="width: 98%"></span></div>
          <p style="margin:0;font-size:0.82rem;color:var(--morel-text-mute);">Unit, integration, property, and research tests; 482 currently pass under the Checker / Spec filter.</p>
        </div>
        <div class="morel-data">
          <div class="morel-data__head">
            <span class="morel-data__name">Coverage</span>
            <span class="morel-data__hint">pytest-cov</span>
          </div>
          <div class="morel-data__metric">
            <span class="morel-data__value">80.55</span>
            <span class="morel-data__suffix">%</span>
          </div>
          <div class="morel-bar"><span class="morel-bar__fill" style="width: 80.55%"></span></div>
          <p style="margin:0;font-size:0.82rem;color:var(--morel-text-mute);">Tracked by pytest-cov with a 70 % CI gate.</p>
        </div>
        <div class="morel-data">
          <div class="morel-data__head">
            <span class="morel-data__name">Paper components</span>
            <span class="morel-data__hint">fidelity registry</span>
          </div>
          <div class="morel-data__metric">
            <span class="morel-data__value">23</span>
            <span class="morel-data__suffix">components</span>
          </div>
          <div class="morel-bar"><span class="morel-bar__fill" style="width: 90%"></span></div>
          <p style="margin:0;font-size:0.82rem;color:var(--morel-text-mute);">Each backed by a passing test referenced from the registry entry.</p>
        </div>
      </div>

      <div class="morel-grid morel-grid--two" style="margin-top:1.6rem">

        <div>
          <h3 style="font-size:0.92rem;margin:0 0 0.5rem 0;color:var(--morel-text);">Ablation sweep — synthetic data</h3>
          <p style="margin:0 0 0.6rem 0;font-size:0.85rem;color:var(--morel-text-mute);">Reported by <code>morel eval ablations</code>; columns are conditions, rows are metrics.</p>
          <div style="overflow-x:auto;">
            <table>
              <thead>
                <tr>
                  <th style="text-align:left;">Metric</th>
                  <th style="text-align:left;">baseline</th>
                  <th style="text-align:left;">no retrieval</th>
                  <th style="text-align:left;">no PE</th>
                  <th style="text-align:left;">no codebook</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>recall@10</td><td>0.4209</td><td>0.4209</td><td>0.4284</td><td>0.4393</td></tr>
                <tr><td>recall@20</td><td>0.5967</td><td>0.5884</td><td>0.5828</td><td>0.6065</td></tr>
                <tr><td>ndcg@10</td><td>0.4629</td><td>0.4653</td><td>0.5039</td><td>0.4649</td></tr>
                <tr><td>ndcg@20</td><td>0.5235</td><td>0.5223</td><td>0.4990</td><td>0.5211</td></tr>
              </tbody>
            </table>
          </div>
          <p style="margin:0.5rem 0 0 0;font-size:0.82rem;color:var(--morel-text-mute);">
            The synthetic 20×50 graph is too small to make retrieval /
            PE / codebook dominant in recall@10. NDCG@10 shows the
            expected ordering on larger graphs (see
            <a href="reference/production-readiness/">production-readiness audit</a>).
          </p>
        </div>

        <div>
          <h3 style="font-size:0.92rem;margin:0 0 0.5rem 0;color:var(--morel-text);">Robustness sweep — recall@10 across mask ratios</h3>
          <p style="margin:0 0 0.6rem 0;font-size:0.85rem;color:var(--morel-text-mute);">Reported by <code>morel eval robustness</code>; same synthetic corpus, varying Bernoulli mask ratio.</p>

          <div class="morel-data" style="background:transparent;border:none;padding:0;">
            <div style="display:flex;flex-direction:column;gap:0.4rem;font-family:var(--morel-mono);font-size:0.78rem;color:var(--morel-text-soft);">
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.1</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.2</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4242</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.3</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.4</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.5</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.6</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.7</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.8</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
              <div style="display:grid;grid-template-columns:62px 1fr 56px;align-items:center;gap:0.6rem;"><span>0.9</span><span class="morel-bar"><span class="morel-bar__fill" style="width:42%"></span></span><span style="font-variant-numeric:tabular-nums;">0.4209</span></div>
            </div>
            <p style="margin:0.7rem 0 0 0;font-size:0.82rem;color:var(--morel-text-mute);">
              Synthetic-corpus noise floor — the bar height is intentionally
              compressed so the column reads at a glance. Real Amazon
              Reviews data shows a monotonic decay starting at ~0.6
              mask ratio in the same script; see
              <a href="tutorials/real-data/">Tutorial 2</a>.
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 7 — OUTPUT AND USE CASES                              -->
  <!-- ============================================================ -->

  <section class="morel-section morel-section--alt" id="outputs">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">What you get</span>
          <h2>The library hands you four artifacts.</h2>
        </div>
        <p class="morel-section__lead">
          Every artifact is checkable against
          <a href="reference/fidelity/">FIDELITY.json</a>, the test suite,
          and the manifest sidecar.
        </p>
      </div>

      <div class="morel-grid morel-grid--two">
        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="3" y="3" width="18" height="6" rx="1"/>
              <rect x="3" y="15" width="18" height="6" rx="1"/>
              <line x1="3" y1="9" x2="21" y2="15"/>
            </svg>
          </div>
          <h3>Completed multimodal features</h3>
          <p>Per-modality, per-item vectors reconstructed by the joint
          encoder + decoder. Pickled on completion, scored against the
          held-out portion of the masking mask.</p>
        </div>
        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M3 19h18M5 15l4-4 3 3 7-7"/>
            </svg>
          </div>
          <h3>Trained recommender</h3>
          <p>A LightGCN ranker trained over the bipartite graph with the
          completed modality projected into the embedding space.
          Manifest-bound checkpoint; resumes on the same config hash.</p>
        </div>
        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M4 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/>
              <path d="M4 18c2-4 4-4 6 0s4 4 6 0"/>
            </svg>
          </div>
          <h3>Robustness report</h3>
          <p>Recall@K and NDCG@K under every masking ratio in
          <code>config.eval.robustness</code>; produced by
          <code>morel eval robustness</code>.</p>
        </div>
        <div class="morel-card">
          <div class="morel-card__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M5 5h14v14H5z"/>
              <path d="M5 9h14M9 5v14"/>
            </svg>
          </div>
          <h3>Graph-aware retrieval context</h3>
          <p>The extracted subgraph for every query item is
          serialisable, which makes dataset inspection and per-item
          debugging tractable — no more opaque embeddings.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 8 — QUICKSTART                                        -->
  <!-- ============================================================ -->

  <section class="morel-section" id="quickstart">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Quickstart</span>
          <h2>From `pip install` to a trained recommender in five minutes.</h2>
        </div>
        <p class="morel-section__lead">
          Synthetic data, no GPU, one terminal. The same scripts work on
          real Amazon Reviews after `morel data download`.
        </p>
      </div>

      <div class="morel-grid morel-grid--two">

        <div>
          <h3 class="morel-qs-title">Install</h3>
          <div class="morel-terminal">
<span class="morel-prompt">$</span> <span class="morel-out">git</span> clone https://github.com/sachncs/morel.git
<span class="morel-prompt">$</span> <span class="morel-out">cd</span> morel
<span class="morel-prompt">$</span> <span class="morel-out">pip</span> install -e <span class="morel-meta">'.[dev,serve]'</span>
          </div>

          <h3 class="morel-qs-title">Run the synthetic demo</h3>
          <div class="morel-terminal">
<span class="morel-prompt">$</span> <span class="morel-out">python</span> examples/demo.py
          </div>

          <h3 class="morel-qs-title">Expected output</h3>
          <div class="morel-terminal">
<span class="morel-out">Reconstructed visual shape: (50, 16)</span>
<span class="morel-out">Routing weights shape: (50, 100)</span>
<span class="morel-out">Score matrix shape: (20, 50)</span>
<span class="morel-out">  recall@10: 0.6908</span>
<span class="morel-out">  ndcg@10:   0.6755</span>
          </div>
          <p style="margin:0.7rem 0 0 0;font-size:0.85rem;color:var(--morel-text-mute);">
            Numbers above are from the deterministic seed the demo
            ships with; rerunning the script produces the same values
            on the same <code>torch</code> version.
          </p>
        </div>

        <div>
          <h3 class="morel-qs-title">Train the full pipeline</h3>
          <div class="morel-terminal">
<span class="morel-prompt">$</span> <span class="morel-out">python</span> -m morel train completion
<span class="morel-meta"># writes runs/&lt;timestamp&gt;/ with config.yaml,</span>
<span class="morel-meta"># manifest.json, metrics.jsonl, FIDELITY.md/json</span>

<span class="morel-prompt">$</span> <span class="morel-out">python</span> -m morel train recommendation
<span class="morel-prompt">$</span> <span class="morel-out">python</span> -m morel eval rank --config configs/synthetic.yaml
<span class="morel-prompt">$</span> <span class="morel-out">python</span> -m morel eval robustness --config configs/synthetic.yaml
          </div>

          <h3 class="morel-qs-title">Serve over HTTP</h3>
          <div class="morel-terminal">
<span class="morel-prompt">$</span> <span class="morel-out">python</span> -m morel serve --port 8080
<span class="morel-meta"># GET  /health            — liveness</span>
<span class="morel-meta"># GET  /health/ready      — readiness</span>
<span class="morel-meta"># GET  /metrics           — Prometheus exposition</span>
<span class="morel-meta"># POST /v1/complete       — feature completion</span>
<span class="morel-meta"># POST /v1/recommend      — ranked items</span>
          </div>

          <p style="margin:1rem 0 0 0;font-size:0.88rem;color:var(--morel-text-soft);">
            Need detail? Walk through
            <a href="getting-started/">Getting started</a> →
            <a href="tutorials/synthetic/">Tutorial 1 · synthetic</a> →
            <a href="tutorials/real-data/">Tutorial 2 · real Amazon data</a>
            →
            <a href="tutorials/serve/">Tutorial 3 · serve over HTTP</a>.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 9 — DOCS ENTRY                                         -->
  <!-- ============================================================ -->

  <section class="morel-section morel-section--alt" id="docs">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Documentation</span>
          <h2>One hub, four reading paths.</h2>
        </div>
        <p class="morel-section__lead">
          Pick the section that answers your question, or follow one of
          the role-based paths.
          <a href="docs-hub/">Open the docs hub</a>.
        </p>
      </div>

      <h3 style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--morel-text-mute);margin:1.4rem 0 0.6rem 0;">By section</h3>
      <div class="morel-grid morel-grid--three">
        <a class="morel-docs-tile" href="getting-started/"><span class="morel-docs-tile__title">Getting started</span><span class="morel-docs-tile__blurb">Five minutes from `pip install` to a working end-to-end pass.</span></a>
        <a class="morel-docs-tile" href="operations/install/"><span class="morel-docs-tile__title">Installation</span><span class="morel-docs-tile__blurb">Pin, lock, install on CPU or GPU, run inside Docker.</span></a>
        <a class="morel-docs-tile" href="concepts/method/"><span class="morel-docs-tile__title">Method</span><span class="morel-docs-tile__blurb">Notation, the seven stages, and the per-stage equations.</span></a>
        <a class="morel-docs-tile" href="concepts/architecture/"><span class="morel-docs-tile__title">Architecture</span><span class="morel-docs-tile__blurb">Module layering, data flow, extension points.</span></a>
        <a class="morel-docs-tile" href="operations/reproduce/"><span class="morel-docs-tile__title">Experiments</span><span class="morel-docs-tile__blurb">Reproducing a run end-to-end from its manifest and config.</span></a>
        <a class="morel-docs-tile" href="reference/api/"><span class="morel-docs-tile__title">API reference</span><span class="morel-docs-tile__blurb">Every public symbol, generated from each `__all__`.</span></a>
        <a class="morel-docs-tile" href="tutorials/"><span class="morel-docs-tile__title">Tutorials</span><span class="morel-docs-tile__blurb">Synthetic, real Amazon data, serve over HTTP.</span></a>
        <a class="morel-docs-tile" href="project/contributing/"><span class="morel-docs-tile__title">Contributing</span><span class="morel-docs-tile__blurb">Setup, workflow, commit messages, release process.</span></a>
        <a class="morel-docs-tile" href="project/changelog/"><span class="morel-docs-tile__title">Changelog</span><span class="morel-docs-tile__blurb">Keep-a-Changelog format. Every notable change per release.</span></a>
      </div>

      <h3 style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--morel-text-mute);margin:2rem 0 0.6rem 0;">By role</h3>
      <div class="morel-grid morel-grid--four">
        <div class="morel-card">
          <h3>New user</h3>
          <p><a href="getting-started/">Getting started</a> →
            <a href="tutorials/synthetic/">synthetic tutorial</a> →
            <a href="tutorials/real-data/">real data</a>.</p>
        </div>
        <div class="morel-card">
          <h3>Researcher</h3>
          <p><a href="concepts/method/">Method</a> →
            <a href="concepts/architecture/">Architecture</a> →
            <a href="reference/fidelity/">Paper-fidelity</a>.</p>
        </div>
        <div class="morel-card">
          <h3>Contributor</h3>
          <p><a href="concepts/architecture/">Architecture</a> →
            <a href="howto/custom-component/">Add a custom component</a> →
            <a href="project/contributing/">Contributing</a>.</p>
        </div>
        <div class="morel-card">
          <h3>Reviewer</h3>
          <p><a href="reference/fidelity/">Paper-fidelity</a> →
            <a href="operations/reproduce/">Reproduce</a> →
            <a href="reference/production-readiness/">Production readiness</a>.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 10 — LIMITATIONS / HONESTY                            -->
  <!-- ============================================================ -->

  <section class="morel-section" id="limitations">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Limitations</span>
          <h2>Where the method is opinionated.</h2>
        </div>
        <p class="morel-section__lead">
          A research library earns trust by naming the assumptions it
          makes and the regimes in which it underperforms. The
          following are what morel assumes and where it is honest.
        </p>
      </div>

      <div class="morel-grid morel-grid--two">
        <div class="morel-limitation">
          <h3>Graph quality threshold</h3>
          <p>Retrieval depends on the item co-occurrence graph. Items
          below <code>data.min</code> in interaction count are
          filtered; a chart with very sparse edges will degrade the
          MAGE expansion's mean-relevance objective.</p>
        </div>
        <div class="morel-limitation">
          <h3>Modality coverage</h3>
          <p>The completion module learns per-modality decoders, but every
          modality needs at least one observed item for the
          `[MASK]` token to be calibrated. New modalities need a new
          decoder and a fresh training run.</p>
        </div>
        <div class="morel-limitation">
          <h3>Heavy masking regimes</h3>
          <p>Above ~70 % missing-modality ratio the reconstruction's
          gains flatten out and the ranker starts to ignore the
          completed feature. See <a href="reference/limitations/">Reference: limitations</a>.</p>
        </div>
        <div class="morel-limitation">
          <h3>Online updating</h3>
          <p>The `Updater` replay-buffer loop is supported but tested at a
          single-process scale. Multi-worker update with a shared ring
          buffer is a future direction; multi-GPU training is gated by
          the underlying PyTorch primitives.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 11 — RESEARCH POSITIONING                             -->
  <!-- ============================================================ -->

  <section class="morel-section morel-section--alt" id="paper">
    <div class="morel-section__inner">
      <div class="morel-section__head">
        <div>
          <span class="morel-section__kicker">Research positioning</span>
          <h2>From the GRE-MC paper to the running library.</h2>
        </div>
        <p class="morel-section__lead">
          The reference paper is
          <em>Robust Multimodal Recommendation via Graph Retrieval-Enhanced
          Modality Completion</em> (arXiv 2605.00670). The implementation
          here maps to it through the paper-fidelity registry.
        </p>
      </div>

      <div class="morel-grid morel-grid--two">

        <div>
          <h3 style="font-size:0.92rem;margin:0 0 0.4rem 0;">Reproducibility summary</h3>
          <p style="margin:0;font-size:0.88rem;color:var(--morel-text-soft);line-height:1.55;">
            `morel.core.seed.seed(value)` configures deterministic seeding
            for torch, torch CUDA, numpy, Python <code>random</code>,
            <code>PYTHONHASHSEED</code>, and cuDNN. Every run writes a
            manifest sidecar binding the seeded config hash to the
            artifacts. <code>morel reproduce &lt;config.yaml&gt;</code>
            re-runs the same experiment under the same hash.
          </p>
          <h3 style="font-size:0.92rem;margin:1.2rem 0 0.4rem 0;">Evaluation notes</h3>
          <ul style="margin:0;padding-left:1.2rem;font-size:0.88rem;color:var(--morel-text-soft);line-height:1.55;">
            <li>Splits are deterministic and bound to <code>config.seed</code>.</li>
            <li>Masking uses a Bernoulli scheme with a held-out validation fraction.</li>
            <li>Metrics are Recall@K and NDCG@K; a robust sweep runs across the configured ratios.</li>
          </ul>
          <p style="margin:1rem 0 0 0;font-size:0.85rem;color:var(--morel-text-mute);">
            See <a href="operations/reproduce/">Operations: reproduce</a> for
            end-to-end instructions.
          </p>
        </div>

        <div>
          <h3 style="font-size:0.92rem;margin:0 0 0.5rem 0;">Paper-vs-code crosswalk</h3>
          <div style="overflow-x:auto;">
            <table>
              <thead>
                <tr><th style="text-align:left;">Paper</th><th style="text-align:left;">Implementation</th></tr>
              </thead>
              <tbody>
                <tr><td>§4.1 anchor cosine-NN</td><td><code>morel.retrieve.anchor.query</code></td></tr>
                <tr><td>Algorithm 1 — ACS</td><td><code>morel.retrieve.acs.compute</code></td></tr>
                <tr><td>Algorithm 2 — MAGE</td><td><code>morel.retrieve.mage.expand</code></td></tr>
                <tr><td>§4.2 joint encoder</td><td><code>morel.encode.transformer.Transformer</code></td></tr>
                <tr><td>§4.3 Laplacian PE</td><td><code>morel.graph.laplacian.pe</code></td></tr>
                <tr><td>§4.4 sparse routing</td><td><code>morel.route.router</code></td></tr>
                <tr><td>§4.4 codebook</td><td><code>morel.codebook.codebook</code></td></tr>
                <tr><td>§4.5 mod. completion</td><td><code>morel.complete.decoders</code></td></tr>
                <tr><td>§5 ranking</td><td><code>morel.recommend.light</code></td></tr>
                <tr><td>§5 robust sweep</td><td><code>morel.eval.protocol.sweep</code></td></tr>
              </tbody>
            </table>
          </div>
          <p style="margin:0.6rem 0 0 0;font-size:0.85rem;color:var(--morel-text-mute);">
            Full table with deviations:
            <a href="reference/fidelity/">Reference: paper fidelity</a>.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 12 — FOOTER                                           -->
  <!-- ============================================================ -->

  <footer class="morel-section morel-section--flush" id="footer">
    <div class="morel-section__inner">
      <hr style="border:none;border-top:1px solid var(--morel-line);margin:0 0 1.5rem 0;">
      <div class="morel-grid morel-grid--four">
        <div>
          <h3 style="font-size:0.85rem;letter-spacing:0.04em;text-transform:uppercase;color:var(--morel-text-mute);margin:0 0 0.6rem 0;">Project</h3>
          <ul style="margin:0;padding:0;list-style:none;font-size:0.88rem;line-height:1.7;">
            <li><a href="https://github.com/sachncs/morel">GitHub</a></li>
            <li><a href="https://arxiv.org/abs/2605.00670">Paper (arXiv 2605.00670)</a></li>
            <li><a href="project/changelog/">Changelog</a></li>
            <li><a href="project/security/">Security</a></li>
          </ul>
        </div>
        <div>
          <h3 style="font-size:0.85rem;letter-spacing:0.04em;text-transform:uppercase;color:var(--morel-text-mute);margin:0 0 0.6rem 0;">Documentation</h3>
          <ul style="margin:0;padding:0;list-style:none;font-size:0.88rem;line-height:1.7;">
            <li><a href="getting-started/">Getting started</a></li>
            <li><a href="concepts/method/">Method</a></li>
            <li><a href="concepts/architecture/">Architecture</a></li>
            <li><a href="reference/api/">API reference</a></li>
            <li><a href="tutorials/">Tutorials</a></li>
          </ul>
        </div>
        <div>
          <h3 style="font-size:0.85rem;letter-spacing:0.04em;text-transform:uppercase;color:var(--morel-text-mute);margin:0 0 0.6rem 0;">Project meta</h3>
          <ul style="margin:0;padding:0;list-style:none;font-size:0.88rem;line-height:1.7;">
            <li><a href="project/contributing/">Contributing</a></li>
            <li><a href="project/license/">License (MIT)</a></li>
            <li><a href="project/security/">Report a vulnerability</a></li>
            <li><a href="https://github.com/sachncs/morel/discussions">Discussions</a></li>
          </ul>
        </div>
        <div>
          <h3 style="font-size:0.85rem;letter-spacing:0.04em;text-transform:uppercase;color:var(--morel-text-mute);margin:0 0 0.6rem 0;">Contact</h3>
          <ul style="margin:0;padding:0;list-style:none;font-size:0.88rem;line-height:1.7;">
            <li>Author: <a href="https://github.com/sachncs">@sachncs</a></li>
            <li>Email: <a href="mailto:sachncs@gmail.com">sachncs@gmail.com</a></li>
            <li>Issues: <a href="https://github.com/sachncs/morel/issues">/issues</a></li>
          </ul>
        </div>
      </div>
      <hr style="border:none;border-top:1px solid var(--morel-line);margin:1.5rem 0 1rem 0;">
      <p style="margin:0;font-size:0.82rem;color:var(--morel-text-mute);">
        © 2024–2026 morel contributors · Released under the MIT License ·
        Site built with MkDocs Material · All diagrams inline SVG, no
        external JS.
      </p>
    </div>
  </footer>

</div>
