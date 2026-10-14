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
        <defs>
          <linearGradient id="morel-mark" x1="10" y1="8" x2="54" y2="56" gradientUnits="userSpaceOnUse">
            <stop stopColor="currentColor" />
            <stop offset="1" stopColor="currentColor" stopOpacity="0.58" />
          </linearGradient>
        </defs>
        <path
          d="M32 9 51 20v22L32 53 13 42V20L32 9Z"
          fill="none"
          stroke="url(#morel-mark)"
          strokeWidth="2.2"
          strokeLinejoin="round"
        />
        <path
          d="m13 20 19 11 19-11M32 31v22"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.72"
        />
        <path
          d="M21 25 32 19l11 6-11 6-11-6Z"
          fill="currentColor"
          opacity="0.18"
        />
        <path
          d="M21 25 32 19l11 6-11 6-11-6Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <g fill="currentColor" stroke="#09131a" strokeWidth="1.4">
          <circle cx="13" cy="20" r="3.2" />
          <circle cx="51" cy="20" r="3.2" />
          <circle cx="32" cy="9" r="3.2" />
          <circle cx="32" cy="53" r="3.2" />
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
