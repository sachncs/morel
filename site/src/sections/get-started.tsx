import { motion } from "framer-motion";
import { ArrowRight, Github, Terminal } from "lucide-react";
import { LinkButton } from "../components/button";
import { Section } from "../components/section";
import { SITE } from "../lib/content";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

export function GetStarted() {
  return (
    <Section
      id="get-started"
      className="pb-32"
    >
      <motion.div
        initial={{ opacity: 0, y: 28 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9, ease }}
        className="ring-edge relative overflow-hidden rounded-3xl bg-gradient-to-br from-ink-900 via-ink-950 to-ink-950 p-10 text-white shadow-card sm:p-16"
      >
        {/* Background visuals */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-50"
          style={{
            background:
              "radial-gradient(50% 60% at 20% 0%, rgba(122,126,255,0.30) 0%, rgba(0,0,0,0) 70%), radial-gradient(40% 50% at 90% 100%, rgba(168,85,247,0.30) 0%, rgba(0,0,0,0) 70%)",
          }}
        />
        <svg
          aria-hidden="true"
          viewBox="0 0 800 360"
          className="pointer-events-none absolute inset-0 h-full w-full opacity-25"
          preserveAspectRatio="xMidYMid slice"
        >
          <defs>
            <pattern id="cta-grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="800" height="360" fill="url(#cta-grid)" />
        </svg>

        <div className="relative grid gap-10 lg:grid-cols-[1.4fr_1fr] lg:items-center">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-accent-300">
              Ship in five minutes
            </p>
            <h2 className="mt-4 text-display-xl text-balance font-semibold tracking-tight text-white">
              From <span className="gradient-text">pip install</span> to ranked recommendations.
            </h2>
            <p className="mt-5 max-w-xl text-pretty text-base leading-relaxed text-ink-300 sm:text-lg">
              Clone the repo, install the dev extras, and run the demo on
              synthetic data. The same code path scales to real catalogs and
              to production inference.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <LinkButton
                href={`${SITE.repo}#installation`}
                size="lg"
                variant="primary"
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
                View on GitHub
              </LinkButton>
            </div>
          </div>

          <div className="ring-edge overflow-hidden rounded-2xl bg-ink-950/80 text-ink-100 ring-white/10 backdrop-blur">
            <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.02] px-4 py-2.5 text-xs text-ink-400">
              <span className="inline-flex items-center gap-2 font-mono">
                <Terminal className="h-3.5 w-3.5" />
                morel — quickstart
              </span>
              <span className="font-mono text-[10px]">⌘</span>
            </div>
            <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-[1.75]">
              <code>
                <span className="text-ink-500"># 1. Get the code</span>
                {"\n"}
                <span className="text-violet-300">git clone</span>{" "}
                <span className="text-emerald-300">https://github.com/sachncs/morel</span>
                {"\n"}
                <span className="text-violet-300">cd</span> morel
                {"\n\n"}
                <span className="text-ink-500"># 2. Sandbox it</span>
                {"\n"}
                <span className="text-violet-300">python3</span> -m venv .venv
                {"\n"}
                <span className="text-violet-300">source</span> .venv/bin/activate
                {"\n\n"}
                <span className="text-ink-500"># 3. Install</span>
                {"\n"}
                <span className="text-violet-300">pip</span> install -e{" "}
                <span className="text-emerald-300">".[dev]"</span>
                {"\n\n"}
                <span className="text-ink-500"># 4. Run the demo</span>
                {"\n"}
                <span className="text-violet-300">python</span> examples/demo.py
              </code>
            </pre>
          </div>
        </div>
      </motion.div>
    </Section>
  );
}
