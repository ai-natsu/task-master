// 画面キャプチャ集（docs/SCREEN_CAPTURES.md）用のスクリーンショットを撮影するスクリプト。
//
// 前提: dev サーバー（client:5173 / server:3001）が起動していること。
//   npm run dev:server と npm run dev:client を別々に起動してから、リポジトリ
//   ルートで `node scripts/capture-screens.mjs` を実行する。
//
// 出力: docs/images/*.png（既存があれば上書き）。dev.db は参照のみ（削除操作は
// 実行しない。確認ダイアログはスクショ後に「キャンセル」で閉じる）。
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdirSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "docs", "images");
mkdirSync(OUT, { recursive: true });

const BASE = "http://localhost:5173";
const API = "http://localhost:3001";

const shot = async (page, name, opts = {}) => {
  await page.screenshot({ path: join(OUT, `${name}.png`), ...opts });
  console.log("saved", name);
};

const run = async () => {
  // 対象プロジェクト（最もタスクの多いもの）を API から取得
  const res = await fetch(`${API}/api/projects`);
  const projects = await res.json();
  const target = [...projects].sort((a, b) => (b._count?.tasks ?? 0) - (a._count?.tasks ?? 0))[0];
  const pid = target.id;
  console.log("target project:", target.name, pid);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1360, height: 860 }, deviceScaleFactor: 2 });

  // SCR-01 ダッシュボード
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await page.getByText("ダッシュボード", { exact: true }).first().waitFor();
  await shot(page, "scr-01-dashboard");

  // COM-01 サイドバー（左カラムだけを切り出し）
  await shot(page, "com-01-sidebar", { clip: { x: 0, y: 0, width: 224, height: 860 } });

  // SCR-02 プロジェクト一覧
  await page.goto(`${BASE}/projects`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "新しいプロジェクト" }).waitFor();
  await shot(page, "scr-02-projects");

  // SCR-05 プロジェクト作成モーダル
  await page.getByRole("button", { name: "新しいプロジェクト" }).click();
  await page.getByText("新しいプロジェクト", { exact: true }).last().waitFor();
  await shot(page, "scr-05-project-modal");
  await page.getByRole("button", { name: "キャンセル" }).click();

  // SCR-03 プロジェクト詳細（ツリー）
  await page.goto(`${BASE}/projects/${pid}`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "ツリー" }).waitFor();
  await shot(page, "scr-03-tree");

  // SCR-03 カンバン
  await page.getByRole("button", { name: "カンバン" }).click();
  await page.waitForTimeout(400);
  await shot(page, "scr-03-kanban");

  // SCR-03 ガント
  await page.getByRole("button", { name: "ガント" }).click();
  await page.waitForTimeout(400);
  await shot(page, "scr-03-gantt");

  // SCR-06 タスク作成モーダル（ツリーに戻ってから）
  await page.getByRole("button", { name: "ツリー" }).click();
  await page.getByRole("button", { name: "新しいタスク" }).click();
  await page.getByText("タスクを作成", { exact: true }).waitFor();
  await shot(page, "scr-06-task-modal");
  await page.getByRole("button", { name: "キャンセル" }).click();

  // COM-02 確認ダイアログ（最初のタスクの削除を押す→スクショ→キャンセル）
  const del = page.getByRole("button", { name: "削除" }).first();
  await del.click();
  await page.getByText("を削除", { exact: false }).first().waitFor();
  await shot(page, "com-02-confirm-dialog");
  await page.getByRole("button", { name: "キャンセル" }).click();

  // SCR-04 設定
  await page.goto(`${BASE}/settings`, { waitUntil: "networkidle" });
  await page.getByText("ステータス設定", { exact: true }).waitFor();
  await shot(page, "scr-04-settings");

  await browser.close();
  console.log("done →", OUT);
};

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
