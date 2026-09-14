import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import {
  Code2,
  Cpu,
  GitBranch,
  Layers,
  Settings2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Section } from "../components/section";
import { FEATURES } from "../lib/content";
import { cn } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

const iconMap: Record<string, LucideIcon> = {
  codebook: Code2,
  graph: GitBranch,
  shield: ShieldCheck,
  bolt: Cpu,
  sparkles: Sparkles,
  stack: Layers,
};

const layout: Array<{ className: string; emphasis?: boolean }> = [
  { className: "lg:col-span-7", emphasis: true },
  { className: "lg:col-span-5" },
  { className: "lg:col-span-5" },
  { className: "lg:col-span-7", emphasis: true },
  { className: "lg:col-span-4" },
  { className: "lg:col-span-4" },
  { className: "lg:col-span-4" },
];

function FeatureVisual({ icon }: { icon: string }) {
  switch (icon) {
    case "codebook":
      return (
        <svg viewBox="0 0 360 160" className="h-auto w-full">
          <defs>
            <linearGradient id="feat-cb" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          {Array.from({ length: 5 }).map((_, r) =>
            Array.from({ length: 18 }).map((_, c) => (
              <rect
                key={`${r}-${c}`}
                x={c * 19 + 4}
                y={r * 28 + 10}
                width={14}
                height={20}
                rx={3}
                fill="url(#feat-cb)"
                opacity={
                  ((r * 7 + c * 3) % 11) / 11 * 0.7 + 0.15
                }
              />
            )),
          )}
        </svg>
      );
    case "graph":
      return (
        <svg viewBox="0 0 360 160" className="h-auto w-full">
          <defs>
            <linearGradient id="feat-gr" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
            <radialGradient id="feat-gr-halo" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#7a7eff" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#7a7eff" stopOpacity="0" />
            </radialGradient>
          </defs>
          <g stroke="url(#feat-gr)" strokeWidth={1} fill="none">
            <line x1="180" y1="80" x2="60" y2="30" />
            <line x1="180" y1="80" x2="300" y2="30" />
            <line x1="180" y1="80" x2="60" y2="130" />
            <line x1="180" y1="80" x2="300" y2="130" />
            <line x1="180" y1="80" x2="120" y2="20" />
            <line x1="180" y1="80" x2="240" y2="20" />
            <line x1="180" y1="80" x2="120" y2="140" />
            <line x1="180" y1="80" x2="240" y2="140" />
          </g>
          <circle cx="180" cy="80" r="28" fill="url(#feat-gr-halo)" />
          <circle cx="180" cy="80" r="6" fill="url(#feat-gr)" />
          <g fill="#c4a8ff">
            <circle cx="60" cy="30" r="4" />
            <circle cx="300" cy="30" r="4" />
            <circle cx="60" cy="130" r="4" />
            <circle cx="300" cy="130" r="4" />
            <circle cx="120" cy="20" r="3.2" />
            <circle cx="240" cy="20" r="3.2" />
            <circle cx="120" cy="140" r="3.2" />
            <circle cx="240" cy="140" r="3.2" />
          </g>
        </svg>
      );
    case "shield":
      return (
        <svg viewBox="0 0 360 160" className="h-auto w-full">
          <defs>
            <linearGradient id="feat-sh" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          <g stroke="url(#feat-sh)" strokeWidth={1.2} fill="none">
            <path d="M 30 30 L 180 80 L 330 30" />
            <path d="M 30 130 L 180 80 L 330 130" />
            <line x1="30" y1="30" x2="30" y2="130" />
            <line x1="330" y1="30" x2="330" y2="130" />
          </g>
          <g fill="url(#feat-sh)">
            <circle cx="60" cy="80" r="3" />
            <circle cx="100" cy="60" r="3" />
            <circle cx="140" cy="100" r="3" />
            <circle cx="180" cy="60" r="3" />
            <circle cx="220" cy="100" r="3" />
            <circle cx="260" cy="60" r="3" />
            <circle cx="300" cy="100" r="3" />
          </g>
          <text x="180" y="146" textAnchor="middle" fontSize="10" fontFamily="ui-monospace, monospace" fill="#8a8a98">
            FIDELITY.json · equation registry
          </text>
        </svg>
      );
    case "bolt":
      return (
        <svg viewBox="0 0 360 160" className="h-auto w-full">
          <defs>
            <linearGradient id="feat-bo" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          <g fontFamily="ui-monospace, monospace" fontSize="9" fill="#8a8a98">
            <text x="14" y="22">GET /recommend</text>
          </g>
          <g stroke="rgba(127,127,160,0.4)" strokeWidth="0.5">
            <line x1="14" y1="30" x2="346" y2="30" />
          </g>
          <g fontFamily="ui-monospace, monospace" fontSize="11">
            <text x="14" y="56" fill="#5d57ff">200 OK</text>
            <text x="14" y="78" fill="#474754" className="dark:fill-ink-300">{`{`}</text>
            <text x="32" y="96" fill="#474754">"items": [</text>
            <text x="48" y="114" fill="#7a7eff">"sku-214", "sku-808", "sku-512"</text>
            <text x="32" y="132" fill="#474754">]</text>
            <text x="14" y="150" fill="#474754">{`}`}</text>
          </g>
        </svg>
      );
    case "sparkles":
      return (
        <svg viewBox="0 0 360 160" className="h-auto w-full">
          <defs>
            <linearGradient id="feat-sp" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          <g stroke="url(#feat-sp)" strokeWidth={1.5} fill="none" strokeLinecap="round">
            <path d="M 30 80 Q 100 30 180 80 T 330 80" />
            <path d="M 30 110 Q 100 60 180 110 T 330 110" opacity="0.5" />
            <path d="M 30 50 Q 100 0 180 50 T 330 50" opacity="0.3" />
          </g>
          <g fill="#7a7eff">
            <circle cx="80" cy="58" r="3" />
            <circle cx="160" cy="80" r="3" />
            <circle cx="240" cy="65" r="3" />
            <circle cx="120" cy="100" r="2.4" />
            <circle cx="200" cy="105" r="2.4" />
            <circle cx="280" cy="100" r="2.4" />
          </g>
        </svg>
      );
    case "stack":
      return (
        <svg viewBox="0 0 360 160" className="h-auto w-full">
          <defs>
            <linearGradient id="feat-st" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7a7eff" />
              <stop offset="100%" stopColor="#c4a8ff" />
            </linearGradient>
          </defs>
          <g fontFamily="ui-monospace, monospace" fontSize="11">
            <rect x="40" y="20" width="280" height="22" rx="4" fill="url(#feat-st)" opacity="0.18" />
            <text x="56" y="35" fill="#5d57ff">retrieve.kind = "mage"</text>

            <rect x="40" y="50" width="280" height="22" rx="4" fill="url(#feat-st)" opacity="0.28" />
            <text x="56" y="65" fill="#5d57ff">codebook.size = 100</text>

            <rect x="40" y="80" width="280" height="22" rx="4" fill="url(#feat-st)" opacity="0.45" />
            <text x="56" y="95" fill="#5d57ff">completion.epochs = 100</text>

            <rect x="40" y="110" width="280" height="22" rx="4" fill="url(#feat-st)" opacity="0.7" />
            <text x="56" y="125" fill="#fff">recommend.kind = "light"</text>
          </g>
        </svg>
      );
    default:
      return null;
  }
}

export function Features() {
  return (
    <Section
      id="features"
      eyebrow="What's inside"
      title={
        <>
          Everything you'd build,{" "}
          <span className="gradient-text">composed for you.</span>
        </>
      }
      description="Each module is independently usable and tested. Together they form a coherent pipeline that you can read top-to-bottom."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-12">
        {FEATURES.map((f, i) => {
          const Icon = iconMap[f.icon] ?? Settings2;
          const span = layout[i] ?? { className: "lg:col-span-4" };
          return (
            <motion.article
              key={f.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.7, delay: i * 0.05, ease }}
              className={cn(
                "ring-edge group relative flex flex-col overflow-hidden rounded-2xl bg-white/70 transition hover:bg-white dark:bg-ink-900/40 dark:hover:bg-ink-900/60",
                span.className,
              )}
            >
              <div className="flex flex-1 flex-col p-7 sm:p-8">
                <div className="mb-5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500/15 to-violet-500/10 text-accent-600 ring-1 ring-accent-500/15 dark:text-accent-300">
                  <Icon className="h-5 w-5" strokeWidth={1.6} />
                </div>
                <h3 className="text-display-sm font-semibold tracking-tight text-ink-900 dark:text-white">
                  {f.title}
                </h3>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-ink-600 dark:text-ink-300">
                  {f.body}
                </p>
                <ul className="mt-5 flex flex-wrap gap-2">
                  {f.bullets.map((b) => (
                    <li
                      key={b}
                      className="inline-flex items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 text-[11px] font-medium text-ink-700 ring-1 ring-ink-200/60 dark:bg-white/5 dark:text-ink-200 dark:ring-white/10"
                    >
                      <span className="h-1 w-1 rounded-full bg-accent-500" />
                      {b}
                    </li>
                  ))}
                </ul>
              </div>

              {span.emphasis && (
                <div className="relative border-t border-ink-200/60 bg-gradient-to-b from-ink-50/40 to-transparent px-6 py-6 dark:border-white/5 dark:from-white/[0.02]">
                  <FeatureVisual icon={f.icon} />
                </div>
              )}
            </motion.article>
          );
        })}
      </div>
    </Section>
  );
}
