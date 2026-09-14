import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const BASE = process.env.GITHUB_PAGES ? "/morel/" : "/";

export default defineConfig({
  plugins: [react()],
  base: BASE,
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
    target: "es2020",
  },
  server: {
    host: true,
    port: 5173,
  },
});
