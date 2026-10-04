import { test, expect, type Page } from "@playwright/test";
import { createProject, createTask, uniqueName } from "./helpers";

// 画面遷移のテスト。UT（ロジック）だけでは、ブラウザの履歴・URL・localStorage・モーダルの
// 表示など、ブラウザ依存の動作を守れないため、実ブラウザで通して確認する。
// 番号は docs/BASIC_DESIGN.md の「画面遷移表」の No に対応する。

const sidebar = (page: Page) => page.locator("aside");

/** プロジェクトを作って、タスクを 1 件持つ詳細画面を開く。 */
async function openProjectWithTask(page: Page) {
  const name = await createProject(page);
  await page.getByRole("link", { name, exact: true }).click();
  const title = uniqueName("task");
  await createTask(page, title);
  return { name, title };
}

test("E-7: サイドバーから各画面へ遷移する（No.1〜4）", async ({ page }) => {
  const name = await createProject(page);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();

  await sidebar(page).getByRole("link", { name: "プロジェクト一覧", exact: false }).first().click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(page.getByRole("heading", { name: "プロジェクト一覧" })).toBeVisible();

  await sidebar(page).getByRole("link", { name: "設定" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page.getByRole("heading", { name: "設定", exact: true })).toBeVisible();

  await sidebar(page).getByRole("link", { name: "ダッシュボード" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();

  await sidebar(page).getByRole("link", { name: new RegExp(name) }).click();
  await expect(page).toHaveURL(/\/projects\/[^/]+$/);
  await expect(page.getByRole("heading", { name })).toBeVisible();
});

test("E-8: ダッシュボードのカード・一覧の名前からプロジェクト詳細へ遷移する（No.5・6）", async ({ page }) => {
  const name = await createProject(page);

  // 一覧の行（名前）
  await page.getByRole("link", { name, exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/[^/]+$/);
  await expect(page.getByRole("heading", { name })).toBeVisible();

  // ダッシュボードのカード
  await page.goto("/");
  await page.locator("main a", { hasText: name }).click();
  await expect(page).toHaveURL(/\/projects\/[^/]+$/);
  await expect(page.getByRole("heading", { name })).toBeVisible();
});

test("E-9: ブラウザの戻る・進む・再読み込み・URL の直接入力でも画面を移動できる", async ({ page }) => {
  const name = await createProject(page);
  const projectUrl = await (async () => {
    await page.getByRole("link", { name, exact: true }).click();
    return page.url();
  })();

  await page.goto("/");
  await sidebar(page).getByRole("link", { name: "設定" }).click();
  await expect(page).toHaveURL(/\/settings$/);

  // 戻る → ダッシュボード、進む → 設定
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page.getByRole("heading", { name: "設定", exact: true })).toBeVisible();

  // 再読み込みしても、同じ画面が表示される
  await page.reload();
  await expect(page.getByRole("heading", { name: "設定", exact: true })).toBeVisible();

  // URL の直接入力（プロジェクト詳細）
  await page.goto(projectUrl);
  await expect(page.getByRole("heading", { name })).toBeVisible();
});

test("E-10: プロジェクト詳細で、ツリー・カンバン・ガントの表示を切り替える", async ({ page }) => {
  const { title } = await openProjectWithTask(page);

  const tree = page.getByRole("button", { name: "ツリー", exact: true });
  const kanban = page.getByRole("button", { name: "カンバン", exact: true });
  const gantt = page.getByRole("button", { name: "ガント", exact: true });

  // 既定はツリー（行末の「+サブ」が見える）
  await expect(tree).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "+サブ" }).first()).toBeVisible();

  await kanban.click();
  await expect(kanban).toHaveAttribute("aria-pressed", "true");
  await expect(tree).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByText(title, { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "+サブ" })).toHaveCount(0);

  await gantt.click();
  await expect(gantt).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText(/バーは開始日〜期限の期間を表します/)).toBeVisible();

  await tree.click();
  await expect(page.getByRole("button", { name: "+サブ" }).first()).toBeVisible();
});

test("E-11: モーダルを開く操作（プロジェクト・タスクの作成/編集、No.7〜11）", async ({ page }) => {
  const name = await createProject(page);

  // No.7: 「+ 新しいプロジェクト」→ 作成モーダル
  await page.getByRole("button", { name: "+ 新しいプロジェクト" }).click();
  await expect(page.getByRole("heading", { name: "新しいプロジェクト" })).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();
  await expect(page.getByRole("heading", { name: "新しいプロジェクト" })).toHaveCount(0);

  // No.8: 編集 → 編集モーダル
  const row = page.locator("div.rounded-xl").filter({ hasText: name });
  await row.getByRole("button", { name: "編集" }).click();
  await expect(page.getByRole("heading", { name: "プロジェクトを編集" })).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();

  await page.getByRole("link", { name, exact: true }).click();
  const title = uniqueName("task");

  // No.9: 「+ 新しいタスク」→ 作成モーダル
  await page.getByRole("button", { name: "+ 新しいタスク" }).click();
  await expect(page.getByRole("heading", { name: "タスクを作成" })).toBeVisible();
  await page.getByPlaceholder("タスク名を入力").fill(title);
  await page.getByRole("button", { name: "作成" }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();

  // No.10: ツリー行のクリック → 編集モーダル（行末の「編集」ボタンでも開く）
  await page.getByText(title, { exact: true }).click();
  await expect(page.getByRole("heading", { name: "タスクを編集" })).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();
  await page.getByRole("button", { name: "編集", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "タスクを編集" })).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();

  // No.11: 「+サブ」→ 作成モーダル（親タスクが指定済み）
  await page.getByRole("button", { name: "+サブ" }).first().click();
  await expect(page.getByRole("heading", { name: "タスクを作成" })).toBeVisible();
  // モーダル内の 3 つ目の選択（ステータス・優先度・親タスクの順）が親タスク。画面側のフィルタの選択と区別する
  await expect(page.locator(".fixed select").nth(2).locator("option:checked")).toContainText(title);
  await page.getByRole("button", { name: "キャンセル" }).click();
});

test("E-12: カンバンのカードのクリックと、ガントのダブルクリックで編集モーダルを開く（No.10）", async ({ page }) => {
  const { title } = await openProjectWithTask(page);

  await page.getByRole("button", { name: "カンバン", exact: true }).click();
  await page.getByText(title, { exact: true }).click();
  await expect(page.getByRole("heading", { name: "タスクを編集" })).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();

  await page.getByRole("button", { name: "ガント", exact: true }).click();
  const label = page.getByText(title, { exact: true });
  await label.click(); // シングルクリックでは開かない
  await expect(page.getByRole("heading", { name: "タスクを編集" })).toHaveCount(0);
  await label.dblclick(); // ダブルクリックで開く
  await expect(page.getByRole("heading", { name: "タスクを編集" })).toBeVisible();
});

test("E-13: 削除は確認ダイアログを経由し、キャンセルすると削除されない（No.12）", async ({ page }) => {
  const name = await createProject(page);
  const row = page.locator("div.rounded-xl").filter({ hasText: name });

  await row.getByRole("button", { name: "削除" }).click();
  await expect(page.getByRole("heading", { name: "プロジェクトを削除" })).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();
  await expect(page.getByRole("heading", { name: "プロジェクトを削除" })).toHaveCount(0);
  await expect(page.getByRole("link", { name, exact: true })).toBeVisible();

  await row.getByRole("button", { name: "削除" }).click();
  await page.getByRole("button", { name: "削除する" }).click();
  await expect(page.getByRole("link", { name, exact: true })).toHaveCount(0);
});

test("E-14: 表示言語の切り替えが、画面遷移・再読み込みをまたいで保持される（localStorage）", async ({ page }) => {
  await page.goto("/settings");
  await page.getByLabel("言語 / Language").selectOption("en");

  await expect(sidebar(page).getByRole("link", { name: /Dashboard/ })).toBeVisible();
  await sidebar(page).getByRole("link", { name: /Projects/ }).first().click();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
  await expect(sidebar(page).getByRole("link", { name: /Settings/ })).toBeVisible();
});
