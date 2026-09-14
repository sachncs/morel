import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { Section } from "../components/section";
import { USE_CASES } from "../lib/content";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

export function UseCases() {
  return (
    <Section
      id="use-cases"
      eyebrow="Where it fits"
      title={
        <>
          One pipeline,{" "}
          <span className="gradient-text">many catalogs.</span>
        </>
      }
      description="morel is domain-agnostic by design. Wherever you have a user–item graph with incomplete features, you have a place for it."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {USE_CASES.map((uc, i) => (
          <motion.article
            key={uc.title}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.7, delay: i * 0.06, ease }}
            className="ring-edge group relative flex flex-col overflow-hidden rounded-2xl bg-white/70 transition hover:bg-white dark:bg-ink-900/40 dark:hover:bg-ink-900/60"
          >
            <div className="flex flex-1 flex-col p-7 sm:p-8">
              <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 text-[11px] font-medium text-ink-700 ring-1 ring-ink-200/60 dark:bg-white/5 dark:text-ink-200 dark:ring-white/10">
                <span className="h-1 w-1 rounded-full bg-accent-500" />
                {uc.industry}
              </span>
              <h3 className="mt-5 text-display-sm font-semibold tracking-tight text-ink-900 dark:text-white">
                {uc.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-600 dark:text-ink-300">
                {uc.body}
              </p>
              <div className="mt-6 flex items-end justify-between border-t border-ink-200/60 pt-5 dark:border-white/5">
                <div>
                  <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">
                    {uc.metric.label}
                  </p>
                  <p className="mt-1 text-2xl font-semibold tracking-tight text-ink-900 dark:text-white">
                    {uc.metric.value}
                  </p>
                </div>
                <a
                  href="#get-started"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full text-ink-500 transition group-hover:bg-ink-100 group-hover:text-ink-900 dark:text-ink-400 dark:group-hover:bg-white/5 dark:group-hover:text-white"
                  aria-label="Read more"
                >
                  <ArrowUpRight className="h-4 w-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </a>
              </div>
            </div>
          </motion.article>
        ))}
      </div>
    </Section>
  );
}
