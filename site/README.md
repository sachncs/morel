# morel — product site

Premium product page for [morel](https://github.com/sachncs/morel), built with
Vite + React + TypeScript + Tailwind CSS and deployed to GitHub Pages.

## Stack

- [Vite 5](https://vitejs.dev/) — dev server and production bundler
- [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS 3](https://tailwindcss.com/) — design tokens and utility CSS
- [Framer Motion](https://www.framer.com/motion/) — refined scroll and reveal animations
- [Lucide](https://lucide.dev/) — icon set

## Develop

```bash
pnpm install
pnpm dev          # http://localhost:5173
```

## Type-check and build

```bash
pnpm typecheck
pnpm build        # outputs site/dist
```

The build respects the `GITHUB_PAGES` env var. When set to `1`, asset URLs are
prefixed with `/morel/` so the bundle works under
<https://sachncs.github.io/morel/>. Locally the prefix is `/`, which is what
`vite preview` expects.

## Deploy

`.github/workflows/pages.yml` builds and publishes `site/dist` to GitHub Pages
on every push to `master`. Make sure Pages is enabled for the repository under
**Settings → Pages → Build and deployment: GitHub Actions** (one-time setup).

## Layout

```
site/
├── index.html              Entry HTML
├── public/                 Static assets served at site root
│   ├── favicon.svg
│   ├── morel-mark.svg
│   └── og-image.svg
└── src/
    ├── main.tsx            React entry
    ├── App.tsx             Page composition
    ├── styles.css          Tailwind layers + global tokens
    ├── lib/
    │   ├── content.ts      All editorial copy (single source of truth)
    │   └── utils.ts        cn() and helpers
    ├── components/         Layout primitives (Nav, Footer, Button, …)
    └── sections/           Page sections (Hero, Features, Architecture, …)
```

The product page renders directly from the React tree in `App.tsx`. It does
**not** load content from `docs/` or any markdown — every string lives in
`src/lib/content.ts`.
