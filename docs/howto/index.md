# How-to guides

Short, goal-oriented recipes for common customisations. Each guide
assumes morel is [installed](../getting-started.md).

<div class="morel-feature-grid">
  <div class="morel-feature">
    <h3><a href="configure/">Configure morel</a></h3>
    <p>Every field in the ``Config`` tree, with a plain-English
    explanation and a YAML example.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="custom-component/">Add a custom component</a></h3>
    <p>Plug a new retriever, encoder, router, codebook, completer,
    or recommender into the registry without touching morel code.</p>
  </div>
  <div class="morel-feature">
    <h3><a href="serve/">Serve in production</a></h3>
    <p>Configure auth, rate limits, body limits, and the readiness
    probe in the deployed server.</p>
  </div>
</div>

## Reading order

If you are new to the project, [configure](configure.md) first —
every other recipe assumes you can read and write the `Config` tree.
Then move on to [custom components](custom-component.md) when you
hit a stage that isn't in the shipped set.
