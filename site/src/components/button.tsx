import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "../lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "quiet";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-medium tracking-tight " +
  "transition-all duration-200 will-change-transform select-none " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-500/60 focus-visible:ring-offset-2 " +
  "focus-visible:ring-offset-white dark:focus-visible:ring-offset-ink-950 " +
  "disabled:opacity-50 disabled:pointer-events-none";

const variants: Record<Variant, string> = {
  primary:
    "bg-ink-900 text-white shadow-[0_1px_0_0_rgba(255,255,255,0.1)_inset,0_8px_24px_-12px_rgba(0,0,0,0.5)] " +
    "hover:bg-ink-800 active:scale-[0.985] " +
    "dark:bg-white dark:text-ink-950 dark:hover:bg-ink-100 dark:shadow-[0_1px_0_0_rgba(255,255,255,0.5)_inset,0_8px_24px_-12px_rgba(255,255,255,0.2)]",
  secondary:
    "bg-white/70 text-ink-900 ring-1 ring-ink-200 backdrop-blur " +
    "hover:bg-white hover:ring-ink-300 active:scale-[0.985] " +
    "dark:bg-white/5 dark:text-white dark:ring-white/10 dark:hover:bg-white/10 dark:hover:ring-white/20",
  ghost:
    "text-ink-700 hover:text-ink-900 hover:bg-ink-100 " +
    "dark:text-ink-300 dark:hover:text-white dark:hover:bg-white/5",
  quiet:
    "text-ink-600 hover:text-ink-900 " +
    "dark:text-ink-400 dark:hover:text-white",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-[15px]",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variant = "primary", size = "md", iconLeft, iconRight, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(base, variants[variant], sizes[size], className)}
      {...rest}
    >
      {iconLeft && <span className="inline-flex shrink-0">{iconLeft}</span>}
      <span>{children}</span>
      {iconRight && <span className="inline-flex shrink-0">{iconRight}</span>}
    </button>
  );
});

type LinkButtonProps = {
  href: string;
  variant?: Variant;
  size?: Size;
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
  external?: boolean;
  className?: string;
  children: ReactNode;
  onClick?: () => void;
};

export function LinkButton({
  href,
  variant = "primary",
  size = "md",
  iconLeft,
  iconRight,
  external,
  className,
  children,
  onClick,
}: LinkButtonProps) {
  const isExternal = external ?? /^https?:\/\//.test(href);
  return (
    <a
      href={href}
      onClick={onClick}
      target={isExternal ? "_blank" : undefined}
      rel={isExternal ? "noreferrer noopener" : undefined}
      className={cn(base, variants[variant], sizes[size], className)}
    >
      {iconLeft && <span className="inline-flex shrink-0">{iconLeft}</span>}
      <span>{children}</span>
      {iconRight && <span className="inline-flex shrink-0">{iconRight}</span>}
    </a>
  );
}
