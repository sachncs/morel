import { motion } from "framer-motion";
import { ArrowRight, Github, Sparkles, Star } from "lucide-react";
import { LinkButton } from "../components/button";
import { Pill } from "../components/pill";
import { PipelineDiagram } from "../components/pipeline-diagram";
import { HERO_PILLS, SITE } from "../lib/content";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

const stagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease } },
};

export function Hero() {
  return (
    <section
      id="top"
      className="relative isolate overflow-hidden pb-24 pt-36 sm:pb-32 sm:pt-44"
    >
      {/* Background glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[820px]"
        style={{
          background:
            "radial-gradient(60% 60% at 50% 0%, rgba(122,126,255,0.22) 0%, rgba(168,85,247,0.12) 40%, rgba(0,0,0,0) 75%)",
        }}
      />
      {/* Subtle grid */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 mask-fade-b grid-pattern opacity-40"
      />

      <div className="container relative">
        <motion.div
          initial="hidden"
          animate="show"
          variants={stagger}
          className="mx-auto flex max-w-4xl flex-col items-center text-center"
        >
          <motion.div variants={item}>
            <Pill tone="accent" className="mb-6">
              <Sparkles className="h-3 w-3" />
              GRE-MC architecture · v1.0
            </Pill>
          </motion.div>

          <motion.h1
            variants={item}
            className="text-display-2xl text-balance font-semibold text-ink-900 dark:text-white"
          >
            Robust multimodal recommendation,{" "}
            <span className="gradient-text">one graph at a time.</span>
          </motion.h1>

          <motion.p
            variants={item}
            className="mt-6 max-w-2xl text-pretty text-base leading-relaxed text-ink-600 sm:text-lg sm:leading-[1.6] dark:text-ink-300"
          >
            <strong className="font-semibold text-ink-900 dark:text-white">morel</strong>{" "}
            is an open-source Python library for graph retrieval-enhanced
            modality completion. Feed it a user–item graph with incomplete
            per-item features, and it returns a trained recommender that
            finishes missing modalities before ranking — paper-faithful,
            deterministic, production-ready.
          </motion.p>

          <motion.div
            variants={item}
            className="mt-9 flex flex-wrap items-center justify-center gap-3"
          >
            <LinkButton
              href={`${SITE.repo}#installation`}
              size="lg"
              iconRight={<ArrowRight className="h-4 w-4" />}
            >
              Get started
            </LinkButton>
            <LinkButton
              href={SITE.repo}
              size="lg"
              variant="secondary"
              iconLeft={<Github className="h-4 w-4" />}
              external
            >
              <span className="inline-flex items-center gap-2">
                View on GitHub
                <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-1.5 py-0.5 text-[10px] font-medium text-ink-600 dark:bg-white/10 dark:text-ink-200">
                  <Star className="h-2.5 w-2.5" />
                  star
                </span>
              </span>
            </LinkButton>
          </motion.div>

          <motion.ul
            variants={item}
            className="mt-10 flex flex-wrap items-center justify-center gap-2"
          >
            {HERO_PILLS.map((p) => (
              <li key={p}>
                <Pill tone="outline">{p}</Pill>
              </li>
            ))}
          </motion.ul>
        </motion.div>

        {/* Diagram */}
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.3, ease }}
          className="relative mx-auto mt-20 max-w-5xl"
        >
          <div className="absolute -inset-x-12 -inset-y-8 -z-10 rounded-[28px] bg-gradient-to-b from-white/0 via-accent-500/[0.06] to-white/0 blur-2xl dark:from-ink-950/0 dark:via-accent-500/[0.10] dark:to-ink-950/0" />
          <div className="ring-edge overflow-hidden rounded-3xl bg-white/60 p-2 shadow-card backdrop-blur-xl dark:bg-ink-900/40">
            <div className="rounded-2xl bg-gradient-to-b from-white to-ink-50/60 p-4 dark:from-ink-950 dark:to-ink-900/60">
              <PipelineDiagram />
            </div>
          </div>

          <div className="pointer-events-none absolute -bottom-2 left-1/2 -z-10 h-12 w-3/4 -translate-x-1/2 bg-soft-glow blur-2xl" />
        </motion.div>

        {/* Subtle metadata strip */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.55, ease }}
          className="mx-auto mt-12 flex max-w-3xl flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-ink-500 dark:text-ink-400"
        >
          <span>{SITE.python}</span>
          <span aria-hidden className="h-1 w-1 rounded-full bg-ink-300 dark:bg-ink-700" />
          <span>{SITE.license} license</span>
          <span aria-hidden className="h-1 w-1 rounded-full bg-ink-300 dark:bg-ink-700" />
          <span>arxiv {SITE.arxiv}</span>
          <span aria-hidden className="h-1 w-1 rounded-full bg-ink-300 dark:bg-ink-700" />
          <span>482 tests · 80% coverage</span>
        </motion.div>
      </div>
    </section>
  );
}
