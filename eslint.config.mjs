import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import security from "eslint-plugin-security";
import noUnsanitized from "eslint-plugin-no-unsanitized";
// Prettier は今回見送り（無効化）。整形は各自の裁量とし、ESLint はコード品質のみ担当する。
// 経緯・再有効化手順は docs/STATIC_ANALYSIS.md を参照。
// import stylistic from "@stylistic/eslint-plugin";
// import prettierConfig from "eslint-config-prettier";

export default tseslint.config(
  // ── 対象外 ──────────────────────────────────────────
  {
    ignores: [
      "**/dist/**",
      "**/node_modules/**",
      "**/coverage/**",
      "playwright-report/**",
      "test-results/**",
      "server/prisma/migrations/**",
      ".claude/**",
      "**/playwright/.cache/**",
    ],
  },

  // ── ベース ──────────────────────────────────────────
  js.configs.recommended,

  // ── 型情報つきルール（tsconfig の include 配下に限定：server は src と tests、client は src） ──
  ...tseslint.configs.recommendedTypeChecked.map((c) => ({
    ...c,
    files: ["server/src/**/*.ts", "server/tests/**/*.ts", "client/src/**/*.{ts,tsx}"],
  })),
  {
    files: ["server/src/**/*.ts", "server/tests/**/*.ts", "client/src/**/*.{ts,tsx}"],
    languageOptions: { parserOptions: { projectService: true } },
    rules: {
      "@typescript-eslint/no-floating-promises": "error", // await 漏れ
      // `_` 始まりの未使用引数は許可（Express のエラー処理ミドルウェアは 4 引数が必須）
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      // Promise の誤用検出。arguments/attributes の void 期待チェックは無効化:
      // Express 4 の async ハンドラと JSX の onClick={async} が一律で誤反応するため
      // （前者は各ルートの try/catch、後者は React の設計慣行でカバーされる領域）
      "@typescript-eslint/no-misused-promises": [
        "error",
        {
          checksVoidReturn: {
            arguments: false,
            attributes: false,
          },
        },
      ],
    },
  },

  // ── テストコードの緩和 ──────────────────────────────
  // Supertest の res.body / モックは構造上 any を返すため、
  // any 系ルールをテストで強制するのは非現実的（実装コードでは error のまま）
  {
    files: [
      "**/*.test.{ts,tsx}",
      "e2e/**/*.ts",
      "server/tests/**/*.ts",
      "client/src/test/**/*.{ts,tsx}",
    ],
    rules: {
      "@typescript-eslint/no-unsafe-assignment": "off",
      "@typescript-eslint/no-unsafe-member-access": "off",
      "@typescript-eslint/no-unsafe-call": "off",
      "@typescript-eslint/no-unsafe-return": "off",
      "@typescript-eslint/no-unsafe-argument": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
  },

  // ── src 外の TS（vite.config.ts / playwright.config.ts 等）は型情報なしで ──
  ...tseslint.configs.recommended.map((c) => ({
    ...c,
    files: ["**/*.config.ts", "e2e/**/*.ts", "client/playwright/**/*.{ts,tsx}"],
  })),

  // ── scripts/（Node で動かす補助スクリプト）──────────────
  {
    files: ["scripts/**/*.mjs"],
    languageOptions: { globals: { console: "readonly", process: "readonly", fetch: "readonly" } },
  },

  // ── 共通の品質ルール ──────────────────────────────
  {
    rules: {
      eqeqeq: "error",
      "prefer-const": "error",
    },
  },

  // ── server: セキュリティ（SAST 一次防御） ──────────
  {
    files: ["server/src/**/*.ts"],
    plugins: { security },
    rules: {
      ...security.configs.recommended.rules,
      // 誤検知が多いため無効化（プロパティアクセス全般に反応する）
      "security/detect-object-injection": "off",
    },
  },

  // ── client: React Hooks + XSS ──────────────────────
  {
    files: ["client/src/**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
      "no-unsanitized": noUnsanitized,
    },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "no-unsanitized/method": "error",
      "no-unsanitized/property": "error",
    },
  },

  // ── 整形（Prettier / @stylistic）は今回見送り ──────
  // 当初は Prettier（printWidth 100 / objectWrap: preserve）と、その後段で
  // オブジェクトリテラルを複数行強制する @stylistic/object-curly-newline を
  // 組み合わせる設計だったが、今回は整形レイヤーごと無効化した。
  // ESLint はコード品質（型安全・await 漏れ・セキュリティ）のみを担当する。
  // 整形ポリシーの検討内容と再有効化手順は docs/STATIC_ANALYSIS.md を参照。
  //
  // prettierConfig,                                   // Prettier 衝突ルールの無効化
  // {                                                 // オブジェクト複数行強制
  //   plugins: { "@stylistic": stylistic },
  //   rules: {
  //     "@stylistic/object-curly-newline": [
  //       "error",
  //       {
  //         ObjectExpression: { minProperties: 2, consistent: true },
  //         ObjectPattern: { consistent: true },
  //         ImportDeclaration: { consistent: true },
  //         ExportDeclaration: { consistent: true },
  //       },
  //     ],
  //   },
  // },
);
