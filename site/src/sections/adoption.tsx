import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { LinkButton } from "../components/button";
import { Section } from "../components/section";
import { ADOPTION, SITE } from "../lib/content";
import { cn } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

export function Adoption() {
  return (
    <Section
      id="adoption"
      eyebrow="Adoption"
      title={
        <>
          Start small.{" "}
          <span className="gradient-text">Scale when you need to.</span>
        </>
      }
      description="morel ships as a Python package, a Docker image, and an HTTP service. Pick the surface that fits where you are today."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {ADOPTION.map((plan, i) => (
          <motion.div
            key={plan.title}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.7, delay: i * 0.06, ease }}
            className={cn(
              "ring-edge relative flex flex-col rounded-2xl p-7 sm:p-8",
              plan.highlight
                ? "bg-gradient-to-br from-accent-500/[0.08] via-white to-violet-500/[0.06] ring-1 dark:from-accent-500/[0.12] dark:via-ink-900/60 dark:to-violet-500/[0.10]"
                : "bg-white/70 dark:bg-ink-900/40",
            )}
          >
            {plan.highlight && (
              <span className="absolute -top-3 left-7 inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-accent-500 to-violet-500 px-3 py-1 text-[11px] font-medium text-white shadow-glow">
                Recommended
              </span>
            )}

            <div className="flex items-baseline justify-between">
              <h3 className="text-display-sm font-semibold tracking-tight text-ink-900 dark:text-white">
                {plan.title}
              </h3>
              <p
                className={cn(
                  "text-xl font-semibold tracking-tight",
                  plan.highlight
                    ? "gradient-text"
                    : "text-ink-900 dark:text-white",
                )}
              >
                {plan.price}
              </p>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-ink-600 dark:text-ink-300">
              {plan.description}
            </p>

            <ul className="mt-6 space-y-3">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2.5 text-sm text-ink-700 dark:text-ink-200">
                  <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-accent-500/15 text-accent-600 dark:text-accent-300">
                    <Check className="h-2.5 w-2.5" strokeWidth={3} />
                  </span>
                  {f}
                </li>
              ))}
            </ul>

            <div className="mt-7">
              <LinkButton
                href={plan.href}
                variant={plan.highlight ? "primary" : "secondary"}
                size="md"
                external={plan.href.startsWith("http") && !plan.href.startsWith(SITE.url)}
                className="w-full"
              >
                {plan.cta}
              </LinkButton>
            </div>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}
