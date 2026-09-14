import { type ReactNode } from "react";
import { cn } from "../lib/utils";

type PillProps = {
  children: ReactNode;
  tone?: "default" | "accent" | "outline";
  className?: string;
};

export function Pill({ children, tone = "default", className }: PillProps) {
  const toneClass =
    tone === "accent"
      ? "bg-accent-500/10 text-accent-600 ring-accent-500/20 dark:text-accent-300"
      : tone === "outline"
        ? "bg-transparent text-ink-700 ring-ink-200 dark:text-ink-300 dark:ring-white/15"
        : "bg-ink-100 text-ink-700 ring-ink-200/60 dark:bg-white/5 dark:text-ink-200 dark:ring-white/10";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium tracking-wide ring-1",
        toneClass,
        className,
      )}
    >
      {children}
    </span>
  );
}
