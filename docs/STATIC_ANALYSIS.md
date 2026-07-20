# 静的解析の方針（決定記録）

TaskMaster における静的解析ツールの選定と、その検討過程を残す。
形式は ADR（Architecture Decision Record）に準じる。

- 状態: **採用済み（ESLint）／ Prettier は今回見送り**
- 最終更新: 2026-07-19

## 背景

導入前の状態では、静的解析は各自が手元で `tsc --noEmit` を実行するのみで、
CI にも lint・整形・セキュリティ走査のステップが無かった（テストとビルドのみ）。
コーディング規約も明文化されていなかった。ここを埋めるため、静的解析を
「型」「コード品質(lint)」「セキュリティ(SAST)」「整形(format)」の層で検討した。

## 検討した選択肢と結論

| 項目 | 検討内容 | 結論 |
|---|---|---|
| 型チェック | `tsc --noEmit` を script 化し CI に組み込む | 採用（各 workspace の `tsc`）|
| Lint | ESLint + typescript-eslint（型情報つき `recommendedTypeChecked`）| **採用** |
| セキュリティ(SAST) | `eslint-plugin-security`（server）、`no-unsanitized`（client）、`npm audit`、GitHub CodeQL | ESLint 系を採用。CodeQL/audit は今後 |
| React 固有 | `eslint-plugin-react-hooks`（Hooks 依存配列・規則）| 採用 |
| 整形 | **Prettier**（`printWidth`, `objectWrap` 等）| **今回は見送り（無効化）** |
| 行幅 | Prettier `printWidth` を 80 / 100 / 120 のどれにするか | 100 を想定していたが、Prettier ごと見送り |
| オブジェクトの複数行強制 | `@stylistic/object-curly-newline`（2 プロパティ以上を複数行に）+ Prettier `objectWrap: preserve` の組み合わせ | Prettier に依存する設計のため、Prettier とともに見送り |
| 配列の複数行強制 | `@stylistic/array-element-newline` を追加するか | 見送り（要望として記録） |
| 実行の3層化 | フック（編集直後）→ スキル `/code-style`（一括）→ CI（ゲート）| 採用 |

## Prettier を「今回見送り」とした理由

- 整形の統一は有用だが、初回導入で全ファイルに大きな差分が出る／スタイルが
  Prettier 流に固定される、というチーム合意を要する変更であり、今回の
  スコープからは切り離した。
- 「オブジェクトは複数行、配列は内容に応じて」といった細かな改行制御の要望は、
  Prettier 単体では実現できず（`printWidth` による幅判定が基本）、
  `@stylistic` ルールとの併用が必要になる。この整形ポリシーの作り込みは
  別途あらためて検討する。
- ESLint（コード品質・型安全・セキュリティ）は Prettier と独立して価値があるため、
  こちらのみ先行して採用した。

## 現在の構成（Prettier 無効化後）

- ルール定義: `eslint.config.mjs`
  - ベース: `@eslint/js` recommended
  - `server/src` `client/src`: 型情報つき `recommendedTypeChecked`、
    `no-floating-promises`（await 漏れ）、`no-misused-promises`
    （Express の async ハンドラ・JSX の onClick で誤反応するため
    `checksVoidReturn.{arguments,attributes}` は無効）
  - server: `eslint-plugin-security`（`detect-object-injection` は誤検知が多く無効）
  - client: `react-hooks`、`no-unsanitized`（XSS）
  - テスト（`*.test.ts(x)` / `e2e/` / `src/test/`）: `any` 系ルールを緩和
    （Supertest の `res.body` 等が構造上 `any` を返すため）
- コマンド: `npm run lint` / `npm run lint:fix` / `npm run check`（= `eslint .`）
- 3層運用:
  1. フック `.claude/hooks/style-check.cmd`（PostToolUse × Edit|Write）—
     編集された `.ts`/`.tsx` を ESLint 自動修正し、残エラーを差し戻す
  2. スキル `/code-style` — リポジトリ全体の一括検査・修正
  3. CI（`.github/workflows/ci.yml`）— `npm run check` を実行

> **現状のスコープ**: 今回はツール一式（設定・スキル・フック・CI）の導入のみで、
> 既存プロダクトコード（`client/src` / `server/src` 等）への lint 適用（修正）は
> 行っていない。そのため CI の Lint ステップは `continue-on-error: true` の
> **非ブロッキング（advisory）**とし、結果は表示するが CI を失敗させない。
> フック（編集時の自動修正）とスキル `/code-style` は、今後**新規・変更したファイルから
> 段階的に**適用していく想定。既存コードを一括クリーンアップした後に
> `continue-on-error` を外してマージゲート化する。

整形（Prettier）を見送ったため、`eslint.config.mjs` 内の該当ブロック
（`eslint-config-prettier` と `@stylistic/object-curly-newline`）は
削除せずコメントで残してある。関連 devDependencies（`prettier` /
`eslint-config-prettier` / `@stylistic/eslint-plugin`）もインストール済みのまま
残しており、再有効化を容易にしている。

## Prettier を再有効化するには

1. `package.json` の scripts に整形コマンドを戻す:
   ```jsonc
   "format": "prettier --write .",
   "format:check": "prettier --check .",
   "check": "eslint . && prettier --check ."
   ```
2. リポジトリ直下に `.prettierrc` を作成:
   ```jsonc
   {
     "printWidth": 100,
     "objectWrap": "preserve"
   }
   ```
3. `.prettierignore` を作成:
   ```
   dist
   coverage
   node_modules
   playwright-report
   test-results
   server/prisma/migrations
   package-lock.json
   .claude
   *.cmd
   *.db
   ```
4. `eslint.config.mjs` の冒頭 import と末尾のコメントアウトした
   `prettierConfig` / `@stylistic/object-curly-newline` ブロックを復活させる。
   `object-curly-newline` は必ず `prettierConfig` の「後」に置く（flat config は後勝ち）。
5. フック `.claude/hooks/style-check-file.js` に Prettier 整形ステップを戻す
   （ESLint --fix の前に `prettier --write` を実行）。
6. CI（`ci.yml`）のステップ名を `Lint & format check` に戻す。
7. 導入時は「設定のみ」「一括整形のみ」「CI 変更」でコミットを分け、
   整形だけの巨大差分を機能変更と混ぜないこと。

## 今後の課題（未着手）

- GitHub CodeQL ワークフロー、`npm audit` の CI ゲート、Dependabot 有効化（SAST 拡充）
- 配列の複数行強制（`@stylistic/array-element-newline`）の要否
- 人間のコミットも縛る場合の husky + lint-staged（pre-commit）
