import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const root = path.resolve(__dirname, "../..");

// CI runs the production standalone build; local runs use the dev server so
// failures point at source files. Both are exercised by `npm run test:e2e`.
const webCommand = process.env.CI
  ? "node scripts/serve-standalone.mjs"
  : "npm run dev --workspace @auvyren/web -- --hostname localhost --port 3000";

export default defineConfig({
  testDir: "./e2e",
  globalTeardown: "./e2e/global-teardown.ts",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI
    ? [["list"], ["html", { open: "never" }]]
    : [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } },
      testIgnore: /responsive\.spec\.ts/,
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"] },
      testMatch: /responsive\.spec\.ts/,
    },
  ],
  webServer: [
    {
      command:
        "node scripts/api.mjs -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: root,
      url: "http://127.0.0.1:8000/health/live",
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      env: {
        ...(process.env as Record<string, string>),
        // Authentication limits are covered by the API suite; browser journeys
        // create a handful of accounts per run and must stay repeatable.
        RATE_LIMIT_ENABLED: "false",
      },
    },
    {
      command: webCommand,
      cwd: root,
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 240_000,
    },
  ],
});
