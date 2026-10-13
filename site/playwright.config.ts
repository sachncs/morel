import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.BASE_URL ?? "http://127.0.0.1:4173",
    trace: "retain-on-failure",
  },
  webServer: {
    command: process.env.BASE_URL?.includes("/morel/")
      ? "node scripts/preview-pages.mjs"
      : "pnpm preview --host 127.0.0.1 --port 4173",
    url: process.env.BASE_URL ?? "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI && !process.env.BASE_URL?.includes("/morel/"),
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
