import { defineConfig, devices } from "@playwright/experimental-ct-react";

// UI 部品のテスト（Playwright Component Testing）。部品を実際のブラウザで描画して検証する。
// 対象は src/ 内の *.test.tsx。*.test.ts は Vitest（関数・ロジックの単体テスト）が受け持つ。
export default defineConfig({
  testDir: "./src",
  testMatch: "**/*.test.tsx",
  snapshotDir: "./playwright/__snapshots__",
  timeout: 15_000,
  reporter: [["list"]],
  use: { ctPort: 3100 },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
