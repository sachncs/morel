import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: "1.25rem",
        sm: "1.5rem",
        lg: "2rem",
        xl: "2.5rem",
      },
      screens: {
        "2xl": "1280px",
      },
    },
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        display: [
          "InterDisplay",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
      colors: {
        ink: {
          50: "#f7f7f8",
          100: "#eeeef1",
          200: "#d9d9df",
          300: "#b6b6c0",
          400: "#8a8a98",
          500: "#5f5f6e",
          600: "#474754",
          700: "#34343e",
          800: "#1f1f27",
          900: "#131318",
          950: "#0a0a0e",
        },
        accent: {
          50: "#eef0ff",
          100: "#dee3ff",
          200: "#c4cbff",
          300: "#9ea6ff",
          400: "#7a7eff",
          500: "#5d57ff",
          600: "#4a3df0",
          700: "#3d2fd1",
          800: "#3228a8",
          900: "#2a2384",
        },
        violet: {
          50: "#f6f3ff",
          100: "#ebe5ff",
          200: "#d8ccff",
          300: "#b8a3ff",
          400: "#9573ff",
          500: "#7a4dff",
          600: "#6934e6",
          700: "#5826bf",
          800: "#48219c",
          900: "#3d1f7e",
        },
      },
      letterSpacing: {
        tightest: "-0.04em",
        tighter: "-0.025em",
        tight: "-0.015em",
      },
      fontSize: {
        "display-2xl": ["clamp(3.25rem, 7vw, 5.5rem)", { lineHeight: "0.98", letterSpacing: "-0.035em", fontWeight: "600" }],
        "display-xl": ["clamp(2.75rem, 5.5vw, 4.25rem)", { lineHeight: "1.02", letterSpacing: "-0.03em", fontWeight: "600" }],
        "display-lg": ["clamp(2.25rem, 4.2vw, 3.25rem)", { lineHeight: "1.05", letterSpacing: "-0.025em", fontWeight: "600" }],
        "display-md": ["clamp(1.75rem, 3vw, 2.25rem)", { lineHeight: "1.15", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display-sm": ["clamp(1.375rem, 2vw, 1.625rem)", { lineHeight: "1.2", letterSpacing: "-0.015em", fontWeight: "600" }],
      },
      backgroundImage: {
        "grid-fade": "linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,0.04) 50%, rgba(255,255,255,0) 100%)",
        "hero-glow":
          "radial-gradient(80% 60% at 50% 0%, rgba(99, 102, 241, 0.18) 0%, rgba(168, 85, 247, 0.10) 35%, rgba(0,0,0,0) 70%)",
        "soft-glow":
          "radial-gradient(40% 40% at 50% 50%, rgba(122, 77, 255, 0.18) 0%, rgba(0,0,0,0) 70%)",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,0.04), 0 30px 80px -20px rgba(99,102,241,0.30)",
        card: "0 1px 0 0 rgba(255,255,255,0.06) inset, 0 30px 60px -30px rgba(0,0,0,0.6)",
        ring: "0 0 0 1px rgba(255,255,255,0.08)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        orbit: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.8s cubic-bezier(0.16, 1, 0.3, 1) both",
        shimmer: "shimmer 8s linear infinite",
        orbit: "orbit 22s linear infinite",
        "pulse-glow": "pulseGlow 4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
