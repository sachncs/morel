import { motion } from "framer-motion";
import { Activity, GaugeCircle, TestTube2 } from "lucide-react";
import { Section } from "../components/section";
import { SITE, STATS, VERIFICATION } from "../lib/content";
import { cn, formatNumber } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

function CountUp({ to, suffix = "", decimals = 0 }: { to: number; suffix?: string; decimals?: number }) {
  // Keep the published value truthful before, during, and after viewport
  // animation. Metrics must never appear as zero while an observer or RAF is
  // delayed, throttled, or disabled by the browser.
  return (
    <span className="tabular-nums">
      {formatNumber(Number(to.toFixed(decimals)))}
      {suffix}
    </span>
  );
}

const FEATURED = [
  {
    icon: Activity,
    label: "Recall@10",
    detail: "Compare against a LightGCN baseline on your catalog.",
  },
  {
    icon: GaugeCircle,
    label: "NDCG@10",
    detail: "Report the masking policy, split, and dataset version.",
  },
] as const;

export function Performance() {
  return (
    <Section
      id="performance"
      eyebrow="Performance"
      title={
        <>
          Numbers that{" "}
          <span className="gradient-text">don't move on you.</span>
        </>
      }
      description="The repository ships reproducible benchmark fixtures for forward passes, retrieval, dataset construction, and training. Run them locally on representative hardware before setting a latency budget."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.6, delay: i * 0.05, ease }}
            className="ring-edge rounded-2xl bg-white/70 p-6 dark:bg-ink-900/40"
          >
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">
              {s.label}
            </p>
            <p className="mt-3 text-4xl font-semibold tracking-tight text-ink-900 dark:text-white">
              <CountUp
                to={parseFloat(s.value)}
                decimals={s.value.includes(".") ? 2 : 0}
                suffix={s.value.includes("%") ? "%" : ""}
              />
            </p>
          </motion.div>
        ))}
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-2">
        {FEATURED.map((row, i) => {
          return (
            <motion.div
              key={row.label}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.7, delay: i * 0.08, ease }}
              className="ring-edge relative overflow-hidden rounded-2xl bg-white/70 p-6 dark:bg-ink-900/40 sm:p-8"
            >
              <div className="flex items-start gap-4">
                <row.icon className="mt-1 h-5 w-5 shrink-0 text-accent-500" />
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">
                    {row.label}
                  </p>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-ink-900 dark:text-white">
                    Measure locally
                  </p>
                  <p className="mt-2 text-sm text-ink-600 dark:text-ink-300">
                    {row.detail}
                  </p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-40px" }}
        transition={{ duration: 0.7, ease }}
        className="mt-10 flex items-center justify-center gap-3 text-sm text-ink-500 dark:text-ink-400"
      >
        <TestTube2 className={cn("h-4 w-4 text-accent-500")} />
        Run the suite yourself —{" "}
        <code className="rounded-md bg-ink-100 px-2 py-0.5 font-mono text-xs text-ink-700 dark:bg-white/5 dark:text-ink-200">
          pytest benchmarks/ --benchmark-only
        </code>
        <span className="text-xs">(last verified {VERIFICATION.lastVerified})</span>
      </motion.div>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-ink-500 dark:text-ink-400">
        <a className="underline decoration-ink-300 underline-offset-4 hover:text-accent-600" href={SITE.benchmarks}>
          Benchmark methodology
        </a>
        <a className="underline decoration-ink-300 underline-offset-4 hover:text-accent-600" href={SITE.readiness}>
          Readiness evidence
        </a>
      </div>
    </Section>
  );
}
