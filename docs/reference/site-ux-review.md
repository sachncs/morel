# Site UX/UI review

Review date: 2026-10-15; launch-readiness follow-up: 2026-10-15
Reviewed surface: published `https://sachncs.github.io/morel/`  
Lens: premium product craft, clarity, restraint, and accessibility—an Apple-style
product review, not a visual imitation of Apple branding.

## Executive assessment

The redesign is materially stronger than the former presentation: the opening
screen has a clear outcome-led headline, a distinctive graph mark, a restrained
dark palette, strong contrast, and a credible technical point of view. The
headline now fits a 360px viewport without clipping, and the product/docs
surfaces use the same teal graph identity.

The next level is not more polish or more sections. It is reduction. The page
currently tries to be a landing page, API brochure, benchmark report, research
paper companion, and operations guide at once. A premium product experience
should make one promise immediately, prove it with one memorable interaction,
and move secondary detail behind deliberate paths.

## What is working

- The hero states the category and differentiator in one sentence.
- The tetrahedral logo is simple enough to recognize at small sizes and has a
  useful relationship to the graph subject.
- The near-black surface, off-white type, and teal accent create a coherent
  technical palette; the existing axe/browser gates provide evidence that the
  color treatment is not producing known WCAG failures.
- The primary action is visually dominant and the GitHub action is easy to
  find.
- The page has a strong information architecture: overview, capabilities,
  quickstart, architecture, use cases, and FAQ.
- Mobile navigation, focus behavior, Escape handling, clipboard feedback, and
  reduced-motion behavior are already covered by the browser suite.

## Highest-priority improvements

### 1. Make the first viewport about the user outcome — improved

The hero now leads with the outcome—completing missing modalities and ranking
with graph context—and the mobile headline no longer overruns the viewport.
The page still combines a technical diagram, capability pills, and two actions,
so the next polish pass should continue reducing competing signals.

Recommended change:

- Keep one short promise, one proof point, and one primary action above the fold.
- Move test count, coverage, license, paper ID, and infrastructure badges into a
  compact trust row below the first interaction.
- Keep GitHub as the persistent utility action; consider making it a quieter
  text link after launch telemetry confirms the primary install path.

### 2. Show the product, not only the architecture — partially improved

The page now animates the pipeline and codebook diagrams, but it still does not
let a first-time visitor feel the value of “incomplete features become ranked
recommendations.” Add one small, deterministic before/after interaction or
animated example:

```text
missing modality → graph retrieval → completed embedding → ranked items
```

It should be understandable without reading a paper and should have a static
fallback for reduced-motion users.

### 3. Reduce repeated card grids

The feature, use-case, and architecture sections all use similar
card rhythms. This makes the page long and flattens hierarchy. Keep three
signature proof points, then convert the rest to compact comparison rows or
documentation links.

### 4. Improve typographic calm

The headline is strong, but body copy is frequently dense with compound
technical nouns. Use shorter paragraphs, fewer all-caps eyebrows, and more
generous vertical rhythm. Put the technical qualification after the plain-
language outcome rather than inside the first sentence.

### 5. Make interaction states unmistakable

Architecture stage controls and code tabs should visibly communicate:

- selected versus available;
- what changes when activated;
- keyboard focus and pressed state;
- whether the next action opens documentation or changes content in place.

The current semantics pass the accessibility gate, but premium interaction
quality requires stronger visual feedback than semantic correctness alone.

## Mobile-specific review

The current 360px viewport has a centered hero, a readable primary action, and
no headline clipping. Remaining risks are vertical fatigue and code density:

- the diagram begins near the fold and should not displace the core action;
- pills should wrap without becoming a second navigation bar;
- code should remain horizontally scrollable with a visible affordance and a
  one-tap copy action;
- long technical sections should expose a compact “read the detail” path rather
  than forcing a continuous scroll.

## Trust and content consistency

The site and docs should continue to show a conservative `≥84.57% coverage`
floor when presenting the published baseline, rather than implying that the
floor is the latest local run. Keep the test count synchronized with the
verification script, as it is now 659.

The phrase “ready to validate” is appropriately cautious. Avoid stronger
production language until the explicitly out-of-scope deployment work has
external evidence.

## Recommended refinement sequence

1. Simplify the hero to one promise, one proof interaction, and one primary CTA.
2. Replace one feature-card grid with the deterministic pipeline demonstration.
3. Consolidate trust metrics into one labeled verification strip.
4. Tighten copy and spacing at mobile and desktop breakpoints.
5. Audit selected, focus, hover, reduced-motion, and error states for every
   interactive component.
6. Re-run the existing Playwright, axe, link, and Pages-shaped artifact gates.

The visual direction should remain dark, quiet, and graph-native. The goal is
not additional decoration; it is confidence through focus, proof, and restraint.
