import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    include: ["src/**/*.test.ts"],
    // No global setupFiles: DB setup is opt-in via `import "../test/setup.js"`
    // so pure unit tests (schemas.test.ts) don't pay for a database they
    // never touch.
    // Set before any module (incl. db.ts → PrismaClient) reads it.
    env: {
      DATABASE_URL: "file:./test.db",
    },
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["src/test/**", "src/**/*.test.ts", "src/index.ts"],
      reporter: ["text", "html"],
    },
    // Prisma + a single shared SQLite file: run test files sequentially
    // so parallel suites don't stomp each other's rows.
    fileParallelism: false,
  },
});
