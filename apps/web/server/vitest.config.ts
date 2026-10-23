import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    include: ["tests/**/*.test.ts"],
    // No global setupFiles: DB setup is opt-in via `import "../helpers/setup.js"`
    // so pure unit tests (tests/unit) don't pay for a database they never touch.
    // Set before any module (incl. db.ts → PrismaClient) reads it.
    env: {
      DATABASE_URL: "file:./test.db",
    },
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["src/index.ts"],
      reporter: ["text", "html"],
    },
    // Prisma + a single shared SQLite file: run test files sequentially
    // so parallel suites don't stomp each other's rows.
    fileParallelism: false,
  },
});
