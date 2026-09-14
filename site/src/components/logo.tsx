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
        className="shrink-0"
      >
        <defs>
          <linearGradient id="logoGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#7a7eff" />
            <stop offset="100%" stopColor="#c4a8ff" />
          </linearGradient>
        </defs>
        <g
          stroke="url(#logoGrad)"
          strokeWidth={1.6}
          fill="none"
          strokeLinecap="round"
        >
          <circle cx="32" cy="32" r="22" strokeDasharray="1.8 3.6" opacity="0.35" />
          <circle cx="32" cy="32" r="2.6" fill="url(#logoGrad)" stroke="none" />
          <circle cx="14" cy="20" r="1.8" fill="url(#logoGrad)" stroke="none" />
          <circle cx="50" cy="20" r="1.8" fill="url(#logoGrad)" stroke="none" />
          <circle cx="14" cy="44" r="1.8" fill="url(#logoGrad)" stroke="none" />
          <circle cx="50" cy="44" r="1.8" fill="url(#logoGrad)" stroke="none" />
          <g opacity="0.9">
            <line x1="32" y1="32" x2="14" y2="20" />
            <line x1="32" y1="32" x2="50" y2="20" />
            <line x1="32" y1="32" x2="14" y2="44" />
            <line x1="32" y1="32" x2="50" y2="44" />
            <line x1="32" y1="32" x2="22" y2="12" />
            <line x1="32" y1="32" x2="42" y2="12" />
            <line x1="32" y1="32" x2="22" y2="52" />
            <line x1="32" y1="32" x2="42" y2="52" />
          </g>
          <circle cx="32" cy="32" r="8" strokeDasharray="1.5 1.6" opacity="0.55" />
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
