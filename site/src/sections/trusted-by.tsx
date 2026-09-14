import { Section } from "../components/section";
import { TRUSTED_LOGOS } from "../lib/content";

export function TrustedBy() {
  return (
    <Section className="py-12 sm:py-16" innerClassName="!max-w-6xl">
      <div className="flex flex-col items-center gap-8 text-center">
        <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-ink-500 dark:text-ink-400">
          Built on the shoulders of
        </p>
        <ul className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 sm:gap-x-12">
          {TRUSTED_LOGOS.map((name) => (
            <li
              key={name}
              className="text-sm font-medium tracking-tight text-ink-400 transition hover:text-ink-700 dark:text-ink-500 dark:hover:text-ink-200"
            >
              {name}
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
