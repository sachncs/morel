import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "./theme";
import { cn } from "../lib/utils";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={mounted ? `Switch to ${theme === "dark" ? "light" : "dark"} mode` : "Toggle theme"}
      className={cn(
        "inline-flex h-9 w-9 items-center justify-center rounded-full",
        "border border-ink-200/70 text-ink-700 transition hover:text-ink-900",
        "dark:border-white/10 dark:text-ink-300 dark:hover:text-white",
        "hover:bg-ink-100 dark:hover:bg-white/5",
        className,
      )}
    >
      <Sun
        className={cn(
          "h-4 w-4 transition",
          theme === "dark" ? "rotate-90 scale-0" : "rotate-0 scale-100",
        )}
      />
      <Moon
        className={cn(
          "absolute h-4 w-4 transition",
          theme === "dark" ? "rotate-0 scale-100" : "-rotate-90 scale-0",
        )}
      />
    </button>
  );
}
