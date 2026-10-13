import { cn } from "../lib/utils";

type LogoProps = {
  className?: string;
  size?: number;
  withWordmark?: boolean;
};

export function Logo({ className, size = 28, withWordmark = true }: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg
        viewBox="0 0 64 64"
        width={size}
        height={size}
        aria-hidden="true"
        className="shrink-0 text-accent-600 dark:text-accent-300"
      >
        <path
          d="M10 30c3-11 11-18 22-18s19 7 22 18c-8 5-16 7-22 7S18 35 10 30Z"
          fill="currentColor"
          opacity="0.16"
        />
        <path
          d="M10 30c3-11 11-18 22-18s19 7 22 18c-8 5-16 7-22 7S18 35 10 30Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <g fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.8">
          <path d="M18 27c2 3 3 5 3 8" />
          <path d="M25 25c1 4 2 7 2 10" />
          <path d="M32 24v11" />
          <path d="M39 25c-1 4-2 7-2 10" />
          <path d="M46 27c-2 3-3 5-3 8" />
        </g>
        <path d="M27 35h10l2 14H25l2-14Z" fill="currentColor" opacity="0.9" />
        <path d="M30 49v5M34 49v5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <g fill="currentColor" stroke="white" strokeWidth="1.2" className="dark:stroke-ink-950">
          <circle cx="14" cy="20" r="2.5" />
          <circle cx="50" cy="20" r="2.5" />
          <circle cx="32" cy="10" r="2.5" />
        </g>
      </svg>
      {withWordmark && (
        <span className="font-display text-[1.05rem] font-semibold tracking-tight text-ink-900 dark:text-white">
          morel
        </span>
      )}
    </span>
  );
}
