# Reference

This section is the technical reference for morel — every public
symbol, every CLI flag, every config field, and the cross-cutting
build artifacts (fidelity report, benchmarks, production readiness).

<div class="morel-feature-grid">
  <div class="morel-feature">
    <h3><a href="api/">API reference</a></h3>
    <p>Every export in every public package, generated from each
    module's <code>__all__</code>.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="cli/">CLI reference</a></h3>
    <p>Every subcommand, flag, and example invocation.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="config/">Config reference</a></h3>
    <p>One row per <code>Config</code> field with a plain-English
    description.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="fidelity/">Paper-fidelity report</a></h3>
    <p>Every paper component tied to its implementation and the test
    that proves it.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="benchmarks/">Benchmarks</a></h3>
    <p>How to run the benchmark suite and what each benchmark
    measures.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="production-readiness/">Production readiness</a></h3>
    <p>Audit trail of every change since the pre-1.0 release.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="limitations/">Limitations</a></h3>
    <p>Out-of-scope areas, paper-vs-code approximations, and known
    edge cases.</p>
  </div>
</div>

!!! tip "Auto-generated"
    The API page is regenerated from each module's `__all__`. Do not
    edit ``docs/reference/api.md`` by hand; instead, run
    ``python -m morel.devtools.gen_api docs/reference/api.md`` to
    refresh it.
