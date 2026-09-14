import { Logo } from "./logo";
import { SITE } from "../lib/content";
import { Github } from "lucide-react";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "Overview", href: "#overview" },
      { label: "Features", href: "#features" },
      { label: "Architecture", href: "#architecture" },
      { label: "Performance", href: "#performance" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: SITE.url + "docs/" },
      { label: "Getting started", href: `${SITE.repo}#installation` },
      { label: "Demo notebook", href: `${SITE.repo}blob/master/examples/demo.py` },
      { label: "Changelog", href: `${SITE.repo}blob/master/CHANGELOG.md` },
    ],
  },
  {
    title: "Project",
    links: [
      { label: "GitHub", href: SITE.repo },
      { label: "Issues", href: `${SITE.repo}/issues` },
      { label: "Discussions", href: `${SITE.repo}/discussions` },
      { label: "Citation", href: `${SITE.repo}blob/master/CITATION.cff` },
    ],
  },
  {
    title: "Trust",
    links: [
      { label: "License", href: `${SITE.repo}blob/master/LICENSE` },
      { label: "Security", href: `${SITE.repo}blob/master/SECURITY.md` },
      { label: "Contributing", href: `${SITE.repo}blob/master/CONTRIBUTING.md` },
      { label: "Code of conduct", href: `${SITE.repo}blob/master/CODE_OF_CONDUCT.md` },
    ],
  },
] as const;

export function Footer() {
  return (
    <footer className="relative mt-24 border-t border-ink-200/70 dark:border-white/5">
      <div className="pointer-events-none absolute inset-x-0 -top-32 h-32 bg-gradient-to-t from-ink-50/0 to-transparent dark:from-ink-950/0" />

      <div className="container py-16 sm:py-20">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_2.6fr]">
          <div>
            <Logo />
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-ink-600 dark:text-ink-300">
              An open-source Python library for graph retrieval-enhanced
              modality completion. Paper-faithful, deterministic,
              production-ready.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-2 text-xs text-ink-500 dark:text-ink-400">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 ring-1 ring-ink-200/60 dark:bg-white/5 dark:ring-white/10">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                {SITE.python}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 ring-1 ring-ink-200/60 dark:bg-white/5 dark:ring-white/10">
                {SITE.license} license
              </span>
              <a
                href={SITE.repo}
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 ring-1 ring-ink-200/60 transition hover:bg-ink-200 dark:bg-white/5 dark:ring-white/10 dark:hover:bg-white/10"
              >
                <Github className="h-3 w-3" />
                Star on GitHub
              </a>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            {COLUMNS.map((col) => (
              <div key={col.title}>
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-500 dark:text-ink-400">
                  {col.title}
                </h3>
                <ul className="mt-4 space-y-2.5">
                  {col.links.map((link) => (
                    <li key={link.href}>
                      <a
                        href={link.href}
                        target={/^https?:\/\//.test(link.href) ? "_blank" : undefined}
                        rel={/^https?:\/\//.test(link.href) ? "noreferrer noopener" : undefined}
                        className="text-sm text-ink-700 transition hover:text-ink-900 dark:text-ink-300 dark:hover:text-white"
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 flex flex-col-reverse items-start gap-4 border-t border-ink-200/70 pt-8 text-xs text-ink-500 sm:flex-row sm:items-center sm:justify-between dark:border-white/5 dark:text-ink-400">
          <p>
            Copyright © {new Date().getFullYear()} Sachin. Released under the {SITE.license} license.
          </p>
          <div className="flex items-center gap-5">
            <a href={SITE.url + "docs/"} className="transition hover:text-ink-900 dark:hover:text-white">
              Docs
            </a>
            <a
              href={SITE.repo}
              target="_blank"
              rel="noreferrer noopener"
              className="transition hover:text-ink-900 dark:hover:text-white"
            >
              GitHub
            </a>
            <a
              href={`${SITE.repo}blob/master/CITATION.cff`}
              target="_blank"
              rel="noreferrer noopener"
              className="transition hover:text-ink-900 dark:hover:text-white"
            >
              Cite
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
