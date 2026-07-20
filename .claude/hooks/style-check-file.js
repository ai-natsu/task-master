// PostToolUse フック（Edit|Write）: 編集された .ts/.tsx を 1 ファイルだけ
// ESLint で自動修正し、残ったエラーを stderr + exit 2 で Claude に差し戻す。
// （Prettier は今回見送り。経緯は docs/STATIC_ANALYSIS.md）
// フック自体の不具合で編集作業が止まらないよう、想定外のエラーは
// fail-open（exit 0）で握りつぶす。
//
// 呼び出しは .claude/hooks/style-check.cmd（PATH を通してから node で実行）経由。
"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");

const projectDir = process.env.CLAUDE_PROJECT_DIR || path.resolve(__dirname, "..", "..");

// --- 対象ファイルの収集 -----------------------------------------------------
function collectPaths() {
  const paths = new Set();

  // 1) stdin の JSON（PostToolUse ペイロード）
  try {
    const raw = fs.readFileSync(0, "utf8");
    if (raw.trim()) {
      const data = JSON.parse(raw);
      const ti = data.tool_input || {};
      if (typeof ti.file_path === "string") paths.add(ti.file_path);
      if (Array.isArray(ti.edits)) {
        // MultiEdit 等は file_path を持つ
        if (typeof ti.file_path === "string") paths.add(ti.file_path);
      }
    }
  } catch {
    /* stdin なし・非 JSON は無視 */
  }

  // 2) 環境変数（バージョン差の保険）
  const env = process.env.CLAUDE_FILE_PATHS;
  if (env) env.split(/\s+/).forEach((p) => p && paths.add(p));

  return [...paths];
}

function isTarget(file) {
  if (!/\.(ts|tsx)$/.test(file)) return false;
  const rel = path.relative(projectDir, path.resolve(file));
  if (rel.startsWith("..")) return false; // プロジェクト外
  if (/(^|[\\/])(node_modules|dist|coverage|\.claude)([\\/]|$)/.test(rel)) return false;
  if (/prisma[\\/]migrations/.test(rel)) return false;
  return fs.existsSync(file);
}

// --- ツール実行（同じ node で bin を起動＝PATH 非依存） ---------------------
function run(binRelPath, args, file) {
  const bin = path.join(projectDir, binRelPath);
  return spawnSync(process.execPath, [bin, ...args, file], {
    cwd: projectDir,
    encoding: "utf8",
  });
}

function main() {
  const targets = collectPaths().filter(isTarget);
  if (targets.length === 0) process.exit(0);

  const problems = [];

  for (const file of targets) {
    // ESLint 自動修正 + 残課題を JSON で取得
    const res = run("node_modules/eslint/bin/eslint.js", ["--fix", "--format", "json"], file);
    if (!res.stdout) continue;
    let report;
    try {
      report = JSON.parse(res.stdout);
    } catch {
      continue;
    }
    for (const f of report) {
      for (const m of f.messages) {
        if (m.severity === 2) {
          const rel = path.relative(projectDir, f.filePath);
          problems.push(`${rel}:${m.line}:${m.column} ${m.message} (${m.ruleId})`);
        }
      }
    }
  }

  if (problems.length > 0) {
    process.stderr.write(
      "ESLint が自動修正できないエラーが残っています。修正してください:\n" +
        problems.join("\n") +
        "\n",
    );
    process.exit(2); // stderr が Claude に差し戻される
  }
  process.exit(0);
}

try {
  main();
} catch (e) {
  // フックの不具合で編集を止めない（fail-open）
  process.stderr.write(`[style-check-file] 内部エラーのためスキップ: ${String(e)}\n`);
  process.exit(0);
}
