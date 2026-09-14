import { type ReactNode } from "react";
import { cn } from "../lib/utils";

type SectionProps = {
  id?: string;
  eyebrow?: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  align?: "left" | "center";
  children?: ReactNode;
  className?: string;
  innerClassName?: string;
};

export function Section({
  id,
  eyebrow,
  title,
  description,
  align = "left",
  className,
  innerClassName,
  children,
}: SectionProps) {
  const isCenter = align === "center";
  return (
    <section id={id} className={cn("relative px-4 py-24 sm:px-6 sm:py-32", className)}>
      <div className={cn("container", innerClassName)}>
        {(eyebrow || title || description) && (
          <header
            className={cn(
              "mx-auto mb-16 max-w-3xl",
              isCenter && "text-center",
            )}
          >
            {eyebrow && (
              <div className={cn("mb-5 flex", isCenter && "justify-center")}>
                <span className="inline-flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.18em] text-accent-600 dark:text-accent-300">
                  <span className="h-px w-6 bg-accent-500/40" />
                  {eyebrow}
                </span>
              </div>
            )}
            {title && (
              <h2 className="text-display-lg text-balance text-ink-900 dark:text-white">{title}</h2>
            )}
            {description && (
              <p
                className={cn(
                  "mt-5 text-base leading-relaxed text-ink-600 sm:text-lg sm:leading-[1.6] dark:text-ink-300",
                  "text-pretty",
                )}
              >
                {description}
              </p>
            )}
          </header>
        )}
        {children}
      </div>
    </section>
  );
}
