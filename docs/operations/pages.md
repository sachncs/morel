# Operations — GitHub Pages

The site is built by ``.github/workflows/docs.yml`` and published to
<https://sachncs.github.io/morel/>.

## One-time repo setting

GitHub Pages must be turned on for the repository so the workflow's
``deploy-pages`` action has somewhere to publish. Only a repo admin
can do this from the web UI:

1. Open **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub
   Actions**.
3. Save. (No branch pick is needed once the source is Actions.)

After this is set once, every push to ``master`` rebuilds and
publishes the site automatically.

## Verifying a deployment

The workflow's ``deploy`` job runs against the protected
``github-pages`` environment; check the run summary for the live URL.
The URL is also pinned in ``mkdocs.yml`` (``site_url``) and in
``pyproject.toml`` (``[project.urls] Documentation``).

If the workflow's build job succeeds but the deploy step times out,
verify that Pages is enabled in repo settings — see "One-time repo
setting" above.

## How the workflow works

The ``docs.yml`` workflow has two jobs:

- ``build`` — runs on a fresh ubuntu runner, installs the project
  with ``pip install -e '.[dev]'``, runs ``mkdocs build --strict``,
  and uploads the resulting ``site/`` directory as a Pages artifact.
- ``deploy`` — depends on ``build``, downloads the artifact, and
  publishes it through ``actions/deploy-pages@v4``.

The ``concurrency: group: docs, cancel-in-progress: true`` block
cancels in-progress runs from the same branch, so a fast-follow push
does not race a slow build.

## Local preview

Run ``mkdocs serve`` to preview the docs locally:

```bash
pip install -e '.[dev]'
mkdocs serve
```

The local server picks up edits as you save them.
