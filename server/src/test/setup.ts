import { execSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { beforeAll, beforeEach, afterAll } from "vitest";
import { prisma } from "../db.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const serverRoot = resolve(__dirname, "../..");
const testDbPath = resolve(serverRoot, "test.db");

beforeAll(() => {
  // Fresh test database, schema applied via migrations. DATABASE_URL is
  // injected by vitest.config.ts (test.env) before db.ts constructs Prisma.
  if (existsSync(testDbPath)) rmSync(testDbPath);
  execSync("npx prisma migrate deploy", {
    cwd: serverRoot,
    stdio: "ignore",
    env: { ...process.env, DATABASE_URL: "file:./test.db" },
  });
});

beforeEach(async () => {
  // Order matters: children before parents (FK constraints).
  await prisma.taskTag.deleteMany();
  await prisma.task.deleteMany();
  await prisma.tag.deleteMany();
  await prisma.project.deleteMany();
  await prisma.status.deleteMany();
});

afterAll(async () => {
  await prisma.$disconnect();
});
