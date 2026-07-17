import { defineConfig, devices } from "@playwright/test";

// E2E runs against a dedicated SQLite database (server/e2e.db) so it never
// touches the dev database. globalSetup reinitializes and seeds it; the two
// webServers below are started with the same DATABASE_URL.
const E2E_DATABASE_URL = "file:./e2e.db";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "npm run dev --workspace=server",
      url: "http://localhost:3001/api/health",
      reuseExistingServer: false,
      timeout: 60_000,
      env: { DATABASE_URL: E2E_DATABASE_URL, PORT: "3001" },
    },
    {
      command: "npm run dev --workspace=client",
      url: "http://localhost:5173",
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
