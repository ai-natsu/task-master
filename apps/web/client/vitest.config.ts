import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "node",
    // 関数・ロジックの単体テストだけ（*.test.ts）。UI 部品のテスト（*.test.tsx）は Playwright CT が受け持つ。
    include: ["src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/test/**", "src/**/*.test.{ts,tsx}", "src/main.tsx", "src/types/**"],
      reporter: ["text", "html"],
    },
  },
});
