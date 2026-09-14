import { motion } from "framer-motion";
import { useState } from "react";
import { Section } from "../components/section";
import { PIPELINE_STAGES } from "../lib/content";
import { cn } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

function StageVisual({ stage }: { stage: number }) {
  switch (stage) {
    case 0:
      return (
        <svg viewBox="0 0 600 320" className="h-auto w-full">
          <defs>
            <linearGradient id="ar-stage1" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          <g>
            {/* Users column */}
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <circle
                key={`u${i}`}
                cx="80"
                cy={60 + i * 40}
                r="10"
                fill="url(#ar-stage1)"
                opacity={0.85}
              />
            ))}
            {/* Items column */}
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <circle
                key={`i${i}`}
                cx="280"
                cy={40 + i * 36}
                r="9"
                fill="#c4a8ff"
                opacity={i === 2 || i === 5 ? 0.45 : 0.9}
              />
            ))}
            {/* Edges */}
            <g stroke="url(#ar-stage1)" strokeWidth="0.8" opacity="0.55">
              {[
                [0, 0], [0, 1], [1, 0], [1, 1], [1, 2],
                [2, 1], [2, 3], [3, 3], [3, 4], [4, 4],
                [4, 5], [5, 5], [5, 6], [2, 5],
              ].map(([u, i], k) => (
                <line key={k} x1="92" y1={60 + u * 40} x2="269" y2={40 + i * 36} />
              ))}
            </g>
            {/* Mask overlay */}
            <g>
              {[2, 5].map((i) => (
                <g key={i}>
                  <rect x="269" y={31 + i * 36} width="22" height="18" rx="4" fill="none" stroke="#7a7eff" strokeDasharray="2 2" opacity="0.7" />
                  <text x="280" y={44 + i * 36} textAnchor="middle" fontSize="9" fontFamily="ui-monospace, monospace" fill="#5d57ff">M=0</text>
                </g>
              ))}
            </g>
            <text x="80" y="295" textAnchor="middle" fontSize="11" fontFamily="ui-sans-serif, system-ui" fill="#8a8a98">
              Users (n=6)
            </text>
            <text x="280" y="295" textAnchor="middle" fontSize="11" fontFamily="ui-sans-serif, system-ui" fill="#8a8a98">
              Items (n=7)
            </text>
            <text x="500" y="50" textAnchor="end" fontSize="11" fontFamily="ui-monospace, monospace" fill="#5d57ff">
              mask = bernoulli(0.4)
            </text>
          </g>
        </svg>
      );
    case 1:
      return (
        <svg viewBox="0 0 600 320" className="h-auto w-full">
          <defs>
            <linearGradient id="ar-stage2" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
            <radialGradient id="ar-stage2-halo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#7a7eff" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#7a7eff" stopOpacity="0" />
            </radialGradient>
          </defs>
          <g stroke="url(#ar-stage2)" strokeWidth="0.8" fill="none">
            <line x1="300" y1="160" x2="120" y2="60" />
            <line x1="300" y1="160" x2="480" y2="60" />
            <line x1="300" y1="160" x2="120" y2="260" />
            <line x1="300" y1="160" x2="480" y2="260" />
            <line x1="300" y1="160" x2="200" y2="40" />
            <line x1="300" y1="160" x2="400" y2="40" />
            <line x1="300" y1="160" x2="200" y2="280" />
            <line x1="300" y1="160" x2="400" y2="280" />
            <line x1="300" y1="160" x2="60" y2="160" />
            <line x1="300" y1="160" x2="540" y2="160" />
          </g>
          <circle cx="300" cy="160" r="60" fill="url(#ar-stage2-halo)" />
          <circle cx="300" cy="160" r="14" fill="#fff" stroke="url(#ar-stage2)" strokeWidth="2" />
          <text x="300" y="164" textAnchor="middle" fontSize="11" fontWeight="600" fill="#5d57ff" fontFamily="ui-sans-serif, system-ui">q</text>
          <g fill="#c4a8ff">
            {[
              [120, 60], [480, 60], [120, 260], [480, 260],
              [200, 40], [400, 40], [200, 280], [400, 280],
              [60, 160], [540, 160],
            ].map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r="6" />
            ))}
          </g>
          <text x="300" y="305" textAnchor="middle" fontSize="11" fontFamily="ui-monospace, monospace" fill="#8a8a98">
            Anchor set A_q ∪ ACS ∪ MAGE
          </text>
        </svg>
      );
    case 2:
      return (
        <svg viewBox="0 0 600 320" className="h-auto w-full">
          <defs>
            <linearGradient id="ar-stage3" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          <g>
            {Array.from({ length: 6 }).map((_, r) =>
              Array.from({ length: 16 }).map((_, c) => {
                const o = ((r * 5 + c * 3) % 11) / 11;
                return (
                  <rect
                    key={`${r}-${c}`}
                    x={c * 36 + 16}
                    y={r * 36 + 30}
                    width={26}
                    height={26}
                    rx={5}
                    fill="url(#ar-stage3)"
                    opacity={0.15 + o * 0.75}
                  />
                );
              }),
            )}
          </g>
          <text x="300" y="295" textAnchor="middle" fontSize="11" fontFamily="ui-monospace, monospace" fill="#8a8a98">
            VQ · Gumbel-VQ · usage + balance losses
          </text>
        </svg>
      );
    case 3:
    default:
      return (
        <svg viewBox="0 0 600 320" className="h-auto w-full">
          <defs>
            <linearGradient id="ar-stage4" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#7a7eff" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#c4a8ff" stopOpacity="1" />
            </linearGradient>
          </defs>
          <g>
            {/* Top-K bar chart */}
            {[
              { rank: 1, score: 0.92 },
              { rank: 2, score: 0.81 },
              { rank: 3, score: 0.74 },
              { rank: 4, score: 0.66 },
              { rank: 5, score: 0.58 },
              { rank: 6, score: 0.51 },
              { rank: 7, score: 0.44 },
              { rank: 8, score: 0.38 },
            ].map((row, i) => (
              <g key={row.rank} transform={`translate(${60 + i * 60}, 0)`}>
                <rect x="0" y={20} width="44" height="220" rx="6" fill="url(#ar-stage4)" opacity={0.18 + row.score * 0.7} />
                <text x="22" y="252" textAnchor="middle" fontSize="10" fontFamily="ui-monospace, monospace" fill="#8a8a98">
                  #{row.rank}
                </text>
                <text x="22" y={16} textAnchor="middle" fontSize="10" fontWeight="600" fontFamily="ui-monospace, monospace" fill="#5d57ff">
                  {row.score.toFixed(2)}
                </text>
              </g>
            ))}
            <text x="300" y="295" textAnchor="middle" fontSize="11" fontFamily="ui-monospace, monospace" fill="#8a8a98">
              LightGCN ranker · BPR loss · top-K recommendations
            </text>
          </g>
        </svg>
      );
  }
}

export function Architecture() {
  const [active, setActive] = useState(0);
  const stage = PIPELINE_STAGES[active];

  return (
    <Section
      id="architecture"
      eyebrow="Architecture"
      title={
        <>
          The pipeline,{" "}
          <span className="gradient-text">end to end.</span>
        </>
      }
      description="From raw interactions to ranked recommendations in four composable stages. Click through to see what each one does."
    >
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        {/* Steps rail */}
        <ol className="flex flex-row gap-2 overflow-x-auto scrollbar-none lg:flex-col lg:gap-1.5 lg:overflow-visible">
          {PIPELINE_STAGES.map((s, i) => {
            const isActive = i === active;
            return (
              <li key={s.title} className="shrink-0 lg:shrink">
                <button
                  type="button"
                  onClick={() => setActive(i)}
                  className={cn(
                    "group flex w-full items-start gap-3 rounded-2xl p-4 text-left transition",
                    isActive
                      ? "bg-white ring-1 ring-ink-200/70 shadow-card dark:bg-ink-900/60 dark:ring-white/10"
                      : "ring-1 ring-transparent hover:bg-white/60 dark:hover:bg-white/[0.03]",
                  )}
                >
                  <span
                    className={cn(
                      "mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-mono text-xs transition",
                      isActive
                        ? "bg-gradient-to-br from-accent-500 to-violet-500 text-white shadow-glow"
                        : "bg-ink-100 text-ink-600 ring-1 ring-ink-200/60 dark:bg-white/5 dark:text-ink-300 dark:ring-white/10",
                    )}
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="min-w-0">
                    <span
                      className={cn(
                        "block text-sm font-semibold tracking-tight",
                        isActive
                          ? "text-ink-900 dark:text-white"
                          : "text-ink-700 dark:text-ink-300",
                      )}
                    >
                      {s.title}
                    </span>
                    <span className="mt-0.5 block font-mono text-[11px] text-ink-500 dark:text-ink-400">
                      {s.kbd}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ol>

        {/* Stage panel */}
        <motion.div
          key={stage.title}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease }}
          className="ring-edge relative overflow-hidden rounded-3xl bg-white/70 p-6 dark:bg-ink-900/40 sm:p-10"
        >
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-accent-500/[0.08] to-transparent"
          />
          <div className="relative">
            <div className="grid gap-8 lg:grid-cols-[1fr_1fr] lg:items-center">
              <div>
                <div className="mb-3 flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-accent-600 dark:text-accent-300">
                  <span className="h-px w-6 bg-accent-500/40" />
                  Stage {String(active + 1).padStart(2, "0")}
                </div>
                <h3 className="text-display-md text-balance font-semibold tracking-tight text-ink-900 dark:text-white">
                  {stage.title}
                </h3>
                <p className="mt-4 max-w-md text-pretty text-base leading-relaxed text-ink-600 dark:text-ink-300">
                  {stage.body}
                </p>
                <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-ink-100 px-3 py-1 font-mono text-xs text-ink-700 ring-1 ring-ink-200/60 dark:bg-white/5 dark:text-ink-200 dark:ring-white/10">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent-500" />
                  {stage.kbd}
                </div>
              </div>
              <div className="rounded-2xl bg-gradient-to-b from-white to-ink-50/40 p-4 ring-1 ring-ink-200/60 dark:from-ink-950 dark:to-ink-900/40 dark:ring-white/5">
                <StageVisual stage={active} />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </Section>
  );
}
