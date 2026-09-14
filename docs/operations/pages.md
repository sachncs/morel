# Operations — GitHub Pages

The marketing site lives in `site/` (Vite + React + Tailwind) and is
built and published by `.github/workflows/pages.yml` to
<https://sachncs.github.io/morel/>.

## One-time repo setting

GitHub Pages must be turned on for the repository so the workflow's
`deploy-pages` action has somewhere to publish. Only a repo admin
can do this from the web UI:

1. Open **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub
   Actions**.
3. Save. (No branch pick is needed once the source is Actions.)

After this is set once, every push to `master` rebuilds and
publishes the site automatically.

## Verifying a deployment

The workflow's `deploy` job runs against the protected
`github-pages` environment; check the run summary for the live URL.
The URL is also pinned in `pyproject.toml`
(`[project.urls] Homepage`).

If the workflow's build job succeeds but the deploy step times out,
verify that Pages is enabled in repo settings — see "One-time repo
setting" above.

## How the workflow works

The `pages.yml` workflow has two jobs:

- `build` — runs on a fresh ubuntu runner, sets up Node 20 and pnpm,
  installs the site dependencies with `pnpm install --frozen-lockfile`,
  runs `pnpm build` (with `GITHUB_PAGES=1` so asset URLs are prefixed
  with `/morel/`), and uploads the resulting `site/dist` directory as a
  Pages artifact.
- `deploy` — depends on `build`, downloads the artifact, and
  publishes it through `actions/deploy-pages@v4`.

The `concurrency: group: pages, cancel-in-progress: true` block
cancels in-progress runs from the same branch, so a fast-follow push
does not race a slow build.

## Local preview

Run `pnpm dev` inside `site/` to preview the marketing site locally:

```bash
cd site
pnpm install
pnpm dev          # http://localhost:5173
```

For a production preview:

```bash
pnpm build
GITHUB_PAGES=1 pnpm build   # uses /morel/ asset prefix
pnpm preview
```

The MkDocs documentation in `docs/` is still useful for offline
reference — run `mkdocs serve` from the repo root to browse it
locally — but it is no longer deployed to GitHub Pages.
