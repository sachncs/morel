import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.BASE_URL ?? "http://127.0.0.1:4173/morel/",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "pnpm exec astro preview --host 127.0.0.1 --port 4173 --strictPort",
    url: process.env.BASE_URL ?? "http://127.0.0.1:4173/morel/",
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
