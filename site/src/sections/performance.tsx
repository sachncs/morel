import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Activity, GaugeCircle, Sparkles, TestTube2 } from "lucide-react";
import { Section } from "../components/section";
import { STATS } from "../lib/content";
import { cn, formatNumber } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

function CountUp({ to, suffix = "", decimals = 0 }: { to: number; suffix?: string; decimals?: number }) {
  const ref = useRef<HTMLSpanElement | null>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const duration = 1400;
    const start = performance.now();
    let raf = 0;
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(eased * to);
      if (t < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [inView, to]);

  return (
    <span ref={ref} className="tabular-nums">
      {formatNumber(Number(value.toFixed(decimals)))}
      {suffix}
    </span>
  );
}

const FEATURED = [
  {
    icon: Activity,
    label: "Recall@10",
    baseline: 0.6145,
    morel: 0.7342,
    unit: "",
  },
  {
    icon: GaugeCircle,
    label: "NDCG@10",
    baseline: 0.6364,
    morel: 0.7488,
    unit: "",
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
      description="We benchmark every release against the previous one. A 20% regression in any suite fails CI. Numbers below are from the synthetic benchmark suite that ships with the repo."
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
              <CountUp to={parseFloat(s.value)} suffix={s.value.includes("%") ? "%" : ""} />
            </p>
          </motion.div>
        ))}
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-2">
        {FEATURED.map((row, i) => {
          const delta = ((row.morel - row.baseline) / row.baseline) * 100;
          return (
            <motion.div
              key={row.label}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.7, delay: i * 0.08, ease }}
              className="ring-edge relative overflow-hidden rounded-2xl bg-white/70 p-6 dark:bg-ink-900/40 sm:p-8"
            >
              <div className="flex items-start justify-between gap-6">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">
                    {row.label}
                  </p>
                  <p className="mt-3 text-5xl font-semibold tracking-tight text-ink-900 dark:text-white">
                    <CountUp to={row.morel} decimals={4} />
                  </p>
                  <p className="mt-2 text-sm text-ink-600 dark:text-ink-300">
                    Baseline LightGCN:{" "}
                    <span className="font-mono text-ink-500 dark:text-ink-400">
                      {row.baseline.toFixed(4)}
                    </span>
                  </p>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 ring-1 ring-emerald-500/20 dark:text-emerald-300">
                  <Sparkles className="h-3 w-3" />+{delta.toFixed(1)}%
                </div>
              </div>
              {/* Sparkline */}
              <svg viewBox="0 0 400 80" className="mt-6 h-16 w-full">
                <defs>
                  <linearGradient id="perf-line" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#7a7eff" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#c4a8ff" stopOpacity="1" />
                  </linearGradient>
                </defs>
                <path
                  d="M 0 60 L 50 56 L 100 48 L 150 44 L 200 38 L 250 30 L 300 24 L 350 18 L 400 12"
                  fill="none"
                  stroke="url(#perf-line)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
                <path
                  d="M 0 60 L 50 56 L 100 48 L 150 44 L 200 38 L 250 30 L 300 24 L 350 18 L 400 12 L 400 80 L 0 80 Z"
                  fill="url(#perf-line)"
                  opacity="0.12"
                />
              </svg>
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
      </motion.div>
    </Section>
  );
}
