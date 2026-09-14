import { motion } from "framer-motion";
import { ArrowUpRight, Cpu, Layers, ShieldCheck, Workflow } from "lucide-react";
import { Section } from "../components/section";
import { SITE } from "../lib/content";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

const cards = [
  {
    icon: Layers,
    title: "Four retrieval strategies",
    body: "BFS, anchor, ACS, and MAGE. Pick the trade-off between recall and latency that fits your corpus.",
  },
  {
    icon: Workflow,
    title: "Unified pipeline",
    body: "One entry point — `morel.Pipeline` — drives retrieval, completion, and ranking. Configurable, swappable, observable.",
  },
  {
    icon: Cpu,
    title: "CPU & GPU",
    body: "Runs end-to-end on CPU for moderate corpora. CUDA acceleration kicks in automatically when available.",
  },
  {
    icon: ShieldCheck,
    title: "Fidelity-first",
    body: "Every algorithm ties to a paper equation. The FIDELITY.json report makes the math auditable.",
  },
];

export function Overview() {
  return (
    <Section
      id="overview"
      eyebrow="Product overview"
      title={
        <>
          One library, one pipeline,{" "}
          <span className="gradient-text">one recommender.</span>
        </>
      }
      description="morel consolidates retrieval, completion, and ranking into a single, configurable Python package. You get research-grade fidelity without giving up the engineering surface you need to ship."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c, i) => (
          <motion.div
            key={c.title}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.6, delay: i * 0.06, ease }}
            className="ring-edge group relative flex flex-col rounded-2xl bg-white/70 p-6 transition hover:bg-white dark:bg-ink-900/40 dark:hover:bg-ink-900/60"
          >
            <div className="mb-5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500/15 to-violet-500/10 text-accent-600 ring-1 ring-accent-500/15 dark:text-accent-300">
              <c.icon className="h-5 w-5" strokeWidth={1.6} />
            </div>
            <h3 className="text-display-sm font-semibold tracking-tight text-ink-900 dark:text-white">
              {c.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-600 dark:text-ink-300">
              {c.body}
            </p>
          </motion.div>
        ))}
      </div>

      <div className="mt-10 flex items-center justify-center">
        <a
          href={SITE.url + "docs/"}
          className="group inline-flex items-center gap-1.5 text-sm font-medium text-accent-600 transition hover:text-accent-700 dark:text-accent-300 dark:hover:text-accent-200"
        >
          Read the documentation
          <ArrowUpRight className="h-4 w-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </a>
      </div>
    </Section>
  );
}
