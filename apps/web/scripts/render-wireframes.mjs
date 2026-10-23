// 画面設計書（docs/SCREEN_DESIGN.md）のワイヤーフレームを PNG に書き出すスクリプト。
// 原本は scripts/wireframes/*.html（共通部品は common.css / common.js）。HTML を直したら本スクリプトで
// 画像を再生成する。Mermaid は使わない（GitHub が block-beta を描画せず、細かい配置も表せないため）。
// 図の中の橙色の番号は、入出力項目一覧の項目ID（I-xxxx）の数字部分。
//
// 前提: リポジトリに Playwright（devDependency）が入っていること（Chromium が必要）。追加の導入は不要。
// 実行:
//   node scripts/render-wireframes.mjs
// 出力: docs/images/wf-<名前>.png
import { mkdirSync, readdirSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";
import { chromium } from "@playwright/test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = join(root, "scripts", "wireframes");
const OUT = join(root, "docs", "images");
mkdirSync(OUT, { recursive: true });

const names = readdirSync(SRC)
  .filter((f) => f.endsWith(".html"))
  .map((f) => f.replace(/\.html$/, ""));

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2, viewport: { width: 1100, height: 900 } });
for (const name of names) {
  await page.goto(pathToFileURL(join(SRC, `${name}.html`)).href);
  await page.locator("#frame").screenshot({ path: join(OUT, `wf-${name}.png`) });
  console.log("saved", `wf-${name}.png`);
}
await browser.close();
console.log("done →", OUT);
