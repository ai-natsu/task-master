// 画面設計書（docs/SCREEN_DESIGN.md）内の Mermaid ワイヤーフレームを個別 PNG に
// 書き出すスクリプト。GitHub は experimental な block-beta を描画しないため、
// 図は PNG 画像として埋め込み、Mermaid 原本は <details> に併記する運用。原本を
// 編集したら本スクリプトで画像を再生成する。
//
// 前提: リポジトリに Playwright（devDependency）が入っていること。加えて描画用に
// mermaid をローカルに入れる（package.json は汚さない）:
//   npm i mermaid --no-save
// 実行:
//   node scripts/render-wireframes.mjs
// 出力: docs/images/wf-*.png（docs/SCREEN_DESIGN.md 内の ```mermaid``` を上から順に対応）
import { readFileSync, mkdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { chromium } from "@playwright/test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const mermaidPath = join(root, "node_modules", "mermaid", "dist", "mermaid.min.js");
if (!existsSync(mermaidPath)) {
  console.error("mermaid が見つかりません。先に `npm i mermaid --no-save` を実行してください。");
  process.exit(1);
}

const OUT = join(root, "docs", "images");
mkdirSync(OUT, { recursive: true });

// ```mermaid``` ブロックの登場順 = 画面の並び順
const ids = ["scr-01", "scr-02", "scr-03", "scr-04", "scr-05", "scr-06", "com-01", "com-02"];

const md = readFileSync(join(root, "docs", "SCREEN_DESIGN.md"), "utf8");
const blocks = [...md.matchAll(/```mermaid\n([\s\S]*?)```/g)].map((m) => m[1]);
if (blocks.length !== ids.length) {
  console.error(`Mermaid ブロック数(${blocks.length})と ids(${ids.length}) が一致しません。ids を更新してください。`);
  process.exit(1);
}

const mermaidJs = readFileSync(mermaidPath, "utf8");

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2 });
await page.setContent('<div id="root"></div>');
await page.addScriptTag({ content: mermaidJs });
const svgs = await page.evaluate(async (blocks) => {
  // eslint-disable-next-line no-undef
  mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
  const out = [];
  for (let i = 0; i < blocks.length; i++) {
    // eslint-disable-next-line no-undef
    const { svg } = await mermaid.render("g" + i, blocks[i]);
    out.push(svg);
  }
  return out;
}, blocks);

for (let i = 0; i < svgs.length; i++) {
  await page.setContent(
    `<div id="w" style="display:inline-block;background:#ffffff;padding:8px">${svgs[i]}</div>`,
  );
  await page.locator("#w").screenshot({ path: join(OUT, `wf-${ids[i]}.png`) });
  console.log("saved", `wf-${ids[i]}.png`);
}

await browser.close();
console.log("done →", OUT);
