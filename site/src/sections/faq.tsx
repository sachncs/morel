import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { useState } from "react";
import { Section } from "../components/section";
import { FAQ } from "../lib/content";
import { cn } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <Section
      id="faq"
      eyebrow="FAQ"
      title={
        <>
          Questions,{" "}
          <span className="gradient-text">answered.</span>
        </>
      }
    >
      <div className="mx-auto max-w-3xl divide-y divide-ink-200/70 overflow-hidden rounded-2xl bg-white/70 ring-1 ring-ink-200/70 dark:divide-white/5 dark:bg-ink-900/40 dark:ring-white/10">
        {FAQ.map((row, i) => {
          const isOpen = open === i;
          return (
            <motion.div
              key={row.q}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.04, ease }}
            >
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : i)}
                aria-expanded={isOpen}
                className="flex w-full items-center justify-between gap-6 px-6 py-5 text-left transition hover:bg-ink-50/60 dark:hover:bg-white/[0.02]"
              >
                <span className="text-base font-medium tracking-tight text-ink-900 dark:text-white">
                  {row.q}
                </span>
                <Plus
                  className={cn(
                    "h-4 w-4 shrink-0 text-ink-400 transition",
                    isOpen && "rotate-45 text-accent-500",
                  )}
                />
              </button>
              <div
                className={cn(
                  "grid overflow-hidden transition-all duration-300 ease-out",
                  isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
                )}
              >
                <div className="min-h-0">
                  <p className="px-6 pb-6 pr-12 text-sm leading-relaxed text-ink-600 dark:text-ink-300">
                    {row.a}
                  </p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </Section>
  );
}
