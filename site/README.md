# morel — product site

Product page and documentation site for [morel](https://github.com/sachncs/morel),
built with Astro, React, TypeScript, and Tailwind CSS and deployed to GitHub
Pages in one build.

## Stack

- [Astro](https://astro.build/) — one static build for product and docs routes
- [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS 3](https://tailwindcss.com/) — design tokens and utility CSS
- [Framer Motion](https://www.framer.com/motion/) — refined scroll and reveal animations
- [Lucide](https://lucide.dev/) — icon set

## Develop

```bash
pnpm install
pnpm dev          # http://localhost:4321/morel/
```

## Type-check and build

```bash
pnpm typecheck
pnpm build        # outputs site/dist
```

Astro uses the `/morel/` base path in both local preview and production so the
same route contract is exercised before deployment.

## Deploy

`.github/workflows/pages.yml` builds and publishes `site/dist` to GitHub Pages
on every push to `master`. Make sure Pages is enabled for the repository under
**Settings → Pages → Build and deployment: GitHub Actions** (one-time setup).

## Layout

```
site/
├── astro.config.mjs        Astro build and Pages base path
├── public/                 Static assets served at site root
│   ├── favicon.svg
│   └── og-image.svg
└── src/
    ├── pages/               Product and documentation routes
    ├── layouts/             Documentation shell
    ├── App.tsx              Product page composition
    ├── styles.css          Tailwind layers + global tokens
    ├── lib/
    │   ├── content.ts      All editorial copy (single source of truth)
    │   └── utils.ts        cn() and helpers
    ├── components/         Layout primitives (Nav, Footer, Button, …)
    └── sections/           Page sections (Hero, Features, Architecture, …)
```

The product page renders from the React tree in `App.tsx`. Astro renders the
documentation routes from the Markdown source in the repository, but keeps
the product page copy and interaction model independent from the docs.
