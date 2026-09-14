import { useEffect, useState } from "react";
import { LinkButton } from "./button";
import { Logo } from "./logo";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "../lib/utils";
import { SITE } from "../lib/content";
import { Github, Menu, X } from "lucide-react";

const NAV_ITEMS = [
  { label: "Overview", href: "#overview" },
  { label: "Features", href: "#features" },
  { label: "Architecture", href: "#architecture" },
  { label: "Performance", href: "#performance" },
  { label: "Use cases", href: "#use-cases" },
  { label: "Docs", href: SITE.url + "docs/" },
] as const;

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-ink-200/60 bg-white/70 backdrop-blur-xl dark:border-white/5 dark:bg-ink-950/70"
          : "border-b border-transparent",
      )}
    >
      <div className="container flex h-16 items-center justify-between">
        <a
          href="#top"
          className="flex items-center gap-2 outline-none focus-visible:ring-2 focus-visible:ring-accent-500/60 rounded-md"
        >
          <Logo size={26} />
        </a>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-full px-3 py-1.5 text-[13px] font-medium tracking-tight transition",
                "text-ink-600 hover:text-ink-900 hover:bg-ink-100",
                "dark:text-ink-300 dark:hover:text-white dark:hover:bg-white/5",
              )}
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <a
            href={SITE.repo}
            target="_blank"
            rel="noreferrer noopener"
            className={cn(
              "inline-flex h-9 w-9 items-center justify-center rounded-full transition",
              "border border-ink-200/70 text-ink-700 hover:text-ink-900 hover:bg-ink-100",
              "dark:border-white/10 dark:text-ink-300 dark:hover:text-white dark:hover:bg-white/5",
            )}
            aria-label="morel on GitHub"
          >
            <Github className="h-4 w-4" />
          </a>
          <LinkButton
            href={`${SITE.repo}#installation`}
            size="sm"
            variant="primary"
            className="ml-1"
          >
            Get started
          </LinkButton>
        </div>

        <button
          type="button"
          aria-label="Open menu"
          onClick={() => setOpen(true)}
          className={cn(
            "inline-flex h-9 w-9 items-center justify-center rounded-full md:hidden",
            "border border-ink-200/70 text-ink-700",
            "dark:border-white/10 dark:text-ink-300",
          )}
        >
          <Menu className="h-4 w-4" />
        </button>
      </div>

      {/* Mobile sheet */}
      <div
        className={cn(
          "fixed inset-0 z-50 md:hidden",
          open ? "pointer-events-auto" : "pointer-events-none",
        )}
        aria-hidden={!open}
      >
        <div
          className={cn(
            "absolute inset-0 bg-ink-950/40 backdrop-blur-sm transition-opacity",
            open ? "opacity-100" : "opacity-0",
          )}
          onClick={() => setOpen(false)}
        />
        <div
          className={cn(
            "absolute inset-x-0 top-0 origin-top bg-white p-6 shadow-xl transition-transform dark:bg-ink-950",
            open ? "translate-y-0" : "-translate-y-4",
          )}
        >
          <div className="flex items-center justify-between">
            <Logo />
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <button
                type="button"
                aria-label="Close menu"
                onClick={() => setOpen(false)}
                className={cn(
                  "inline-flex h-9 w-9 items-center justify-center rounded-full",
                  "border border-ink-200/70 text-ink-700",
                  "dark:border-white/10 dark:text-ink-300",
                )}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          <nav className="mt-8 flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "rounded-2xl px-4 py-3 text-base font-medium tracking-tight transition",
                  "text-ink-800 hover:bg-ink-100",
                  "dark:text-white dark:hover:bg-white/5",
                )}
              >
                {item.label}
              </a>
            ))}
          </nav>
          <div className="mt-6 flex flex-col gap-3">
            <LinkButton
              href={SITE.repo}
              size="md"
              variant="secondary"
              external
              iconLeft={<Github className="h-4 w-4" />}
              onClick={() => setOpen(false)}
            >
              View on GitHub
            </LinkButton>
            <LinkButton
              href={`${SITE.repo}#installation`}
              size="md"
              variant="primary"
              onClick={() => setOpen(false)}
            >
              Get started
            </LinkButton>
          </div>
        </div>
      </div>
    </header>
  );
}
