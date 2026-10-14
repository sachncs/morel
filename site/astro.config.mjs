import react from "@astrojs/react";
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://sachncs.github.io/morel/",
  base: "/morel/",
  integrations: [react()],
  build: { format: "directory" },
});
