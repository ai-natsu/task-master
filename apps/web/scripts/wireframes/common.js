// ワイヤーフレーム共通部品。<div data-comp="..."> の位置に、サイドバー・ヘッダーなどを差し込む。
const ID = (n, cls = "") => `<i class="id ${cls}">${n}</i>`;
window.ID = ID;

const PROJECTS = [
  ["#6366f1", "新製品リリース", 12],
  ["#22c55e", "社内ポータル刷新", 8],
  ["#f59e0b", "営業資料の整備", 5],
];

function sidebar(active, ids) {
  const nav = (key, label, id) =>
    `<div class="nav ${active === key ? "on" : ""}">${id ? ID(id) : ""}${label}</div>`;
  const pj = PROJECTS.map(
    ([c, n, k], i) =>
      `<div class="pj ${active === "pj" && i === 0 ? "on" : ""}">${i === 0 && ids ? ID("C105") : ""}<span class="dot" style="background:${c}"></span><span class="trunc">${n}</span><b>${k}</b></div>`
  ).join("");
  return `<aside class="side">
    <div class="logo" style="position:relative">${ids ? ID("C101") : ""}✓ TaskMaster</div>
    <nav>
      ${nav("dashboard", "📊 ダッシュボード", ids ? "C102" : "")}
      ${nav("projects", "📁 プロジェクト一覧", ids ? "C103" : "")}
      <div class="head">${ids ? ID("C104") : ""}プロジェクト一覧</div>
      ${pj}
    </nav>
    <div class="foot"><div class="nav ${active === "settings" ? "on" : ""}" style="margin:0">${ids ? ID("C106") : ""}⚙️ 設定</div></div>
  </aside>`;
}

function titlebar(text) {
  return `<div class="titlebar"><i></i><i></i><i></i><span>${text}</span></div>`;
}

const comps = {
  titlebar: (el) => titlebar(el.dataset.text),
  sidebar: (el) => sidebar(el.dataset.active, el.dataset.ids === "1"),
  // プロジェクト詳細（SCR-03）の上部：ヘッダー・統計・フィルタ
  "pv-top": (el) => {
    const tab = el.dataset.tab;
    const t = (k, l) => `<span class="btn" style="border-radius:8px 8px 0 0;border-color:#94a3b8;${k === tab ? "background:#f8fafc;border-bottom-color:#f8fafc;color:#0f172a" : "background:#cbd5e1;color:#475569"};padding:6px 16px;font-weight:500">${l}</span>`;
    const stats = el.dataset.stats === "1";
    return `
    <div class="row" style="align-items:flex-start;gap:12px;margin-bottom:14px">
      <div style="flex:1;min-width:0;position:relative">${ID("0301")}
        <div class="row"><span class="dot lg" style="background:#6366f1"></span><span style="font-size:16px;font-weight:700;color:#0f172a" class="trunc">新製品リリース</span></div>
        <div class="muted trunc" style="margin-top:3px">来春のリリースに向けた準備タスク一式（長い説明は「...」で省略）</div>
      </div>
      <div class="row" style="gap:10px;align-items:flex-end">
        <span class="btn ghost" style="position:relative">${ID("0302")}統計を${stats ? "隠す" : "表示"}</span>
        <span class="row" style="gap:2px;align-items:flex-end;position:relative">${ID("0303")}${t("tree", "ツリー")}${t("kanban", "カンバン")}${t("gantt", "ガント")}</span>
        <span class="btn primary" style="background:#6366f1">${ID("0304")}+ 新しいタスク</span>
      </div>
    </div>
    ${stats ? `<div class="grid g4" style="margin-bottom:10px;position:relative">${ID("0305")}
      <div class="card"><div class="lb">タスク総数</div><div class="v">24</div></div>
      <div class="card"><div class="lb">完了率</div><div class="v green">38%</div></div>
      <div class="card"><div class="lb">期限超過</div><div class="v red-t">2</div></div>
      <div class="card"><div class="lb">期限が近い（3日後まで）</div><div class="v amber-t">3</div></div></div>
      <div class="grid g2" style="margin-bottom:14px">
        <div class="card"><h3>ステータス別</h3>${["未着手:6", "進行中:8", "レビュー中:1", "完了:9"].map((s) => `<div class="row" style="margin-bottom:4px"><span class="pill s-todo" style="width:70px;text-align:center">${s.split(":")[0]}</span><span class="bar"><i style="width:${Number(s.split(":")[1]) * 4}%"></i></span><span class="small muted">${s.split(":")[1]}</span></div>`).join("")}</div>
        <div class="card"><h3>優先度別</h3>${["緊急:3", "高:6", "中:11", "低:4"].map((s) => `<div class="row" style="margin-bottom:4px"><span class="pill p-low" style="width:70px;text-align:center">${s.split(":")[0]}</span><span class="bar"><i style="width:${Number(s.split(":")[1]) * 6}%"></i></span><span class="small muted">${s.split(":")[1]}</span></div>`).join("")}</div>
      </div>` : ""}
    <div class="row" style="margin-bottom:22px;flex-wrap:wrap">
      <span class="input" style="width:210px">${ID("0306")}タスクを検索...</span>
      <span class="select" style="width:150px">${ID("0307")}すべてのステータス</span>
      <span class="select" style="width:130px">${ID("0308")}すべての優先度</span>
      <span class="select" style="width:120px">${ID("0309")}すべてのタグ</span>
      <span class="small muted" style="position:relative">${ID("0310", "i")}クリア <span class="small">※いずれかの条件を指定したときだけ表示</span></span>
    </div>`;
  },
};

document.querySelectorAll("[data-comp]").forEach((el) => {
  const fn = comps[el.dataset.comp];
  if (fn) el.outerHTML = fn(el);
});
