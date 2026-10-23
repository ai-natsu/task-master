import { execSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { resolve } from "node:path";

// Reset and seed the dedicated E2E database before the servers start.
export default function globalSetup() {
  const serverDir = resolve(__dirname, "../server");
  const dbPath = resolve(serverDir, "e2e.db");
  const env = { ...process.env, DATABASE_URL: "file:./e2e.db" };

  if (existsSync(dbPath)) rmSync(dbPath);
  execSync("npx prisma migrate deploy", { cwd: serverDir, stdio: "inherit", env });
  execSync("npm run seed", { cwd: serverDir, stdio: "inherit", env });
}
