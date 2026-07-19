---
name: code-style
description: コードスタイルの検査と修正。ESLint（型情報つき + セキュリティ + React Hooks）を
  実行し、違反を修正する。コミット前・PR作成前・「lintして」と頼まれたときに使う。
  引数 check で検査のみ、パス指定で範囲限定。
---

# コードスタイルの検査と修正

ESLint によるコード品質の検査と修正を行う。
フック（編集直後の1ファイル自動修正）→ 本スキル（一括仕上げ）→ CI（強制ゲート）の
3層構成の中間を担い、CI と同一コマンド（`npm run check`）を使うことで
「手元で通れば CI も通る」を保証する。

> 整形（Prettier）は今回見送り。ESLint はコード品質のみを担当し、空白・改行などの
> 見た目は各自の裁量とする。経緯と再有効化手順は `docs/STATIC_ANALYSIS.md` を参照。

## 引数の解釈

呼び出し形式: `/code-style [check] [パス]`

| 引数 | モード | 例 |
|---|---|---|
| なし | 修正モード（全体） | `/code-style` |
| `check` | 検査のみ・コード変更なし | `/code-style check` |
| パスのみ | 修正モード（範囲限定） | `/code-style server` |
| `check` + パス | 検査のみ（範囲限定） | `/code-style check client/src` |

- `fix` が渡された場合は既定（修正モード）と同義として扱う
- パスはリポジトリルートからの相対で解釈する（`server` / `client/src/components` 等）

## 修正モードの手順

1. `npm run lint:fix` を実行する（ESLint 自動修正）
   - 範囲限定時は `npx eslint <パス> --fix`
2. 残った ESLint エラー・警告を 1 件ずつ読み、コードを修正する
   - 修正は指摘の解消に必要な最小限にとどめる
3. `npm run check` が全て通るまで 2 を繰り返す
4. コードに変更が生じた場合は `npm test` を実行し、挙動が壊れていないことを確認する
5. 報告する:
   - 自動修正されたファイル数
   - 手動修正の内容（ファイル:行 / ルール名 / 修正方針）
   - 残課題（修正できなかったもの・判断を要するもの）

## check モードの手順

1. `npm run check` を実行する（= `eslint .`、CI と同一の判定）
   - 範囲限定時は `npx eslint <パス>`
2. **コードは一切変更しない**
3. 結果を以下の形式で報告する:

   | 種別 | 件数 | 代表例（ファイル:行 / ルール名） |
   |---|---|---|
   | ESLint error | n | ... |
   | ESLint warn | n | ... |

   最後に総合判定を 1 行で: ✅ CI 通過見込み / ❌ 要修正（修正には `/code-style` を実行）

## 禁止事項

- エラーを消すためだけの `eslint-disable` コメントの追加。
  抑制が本当に必要と判断した場合は、理由を報告してユーザーの承認を得てから行う
- ルール自体の緩和（`eslint.config.mjs` の変更）。
  ルールに問題があると考えた場合は、変更せず別タスクとして提案する
- スタイル修正と無関係なリファクタリングの混入
- check モードでのコード変更

## 補足: このプロジェクトの ESLint ルール

- 型情報つき（`recommendedTypeChecked`）: `no-floating-promises`（await 漏れ）等
- server: `eslint-plugin-security`（SAST 一次防御。`detect-object-injection` は誤検知が多く無効）
- client: `react-hooks` / `no-unsanitized`（XSS）
- テストコード（`*.test.ts(x)` / `e2e/` / `src/test/`）は `any` 系ルールを緩和済み
