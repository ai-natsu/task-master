import { test, expect } from "@playwright/test";
import { createProject, createTask, uniqueName } from "./helpers";

test("E-1: create project, task, and subtask shows hierarchy", async ({ page }) => {
  const name = await createProject(page);
  await page.getByRole("link", { name, exact: true }).click();

  await createTask(page, "親タスク");

  // Add a subtask via the row's "+サブ" action.
  const row = page.locator("div").filter({ hasText: "親タスク" }).last();
  await row.getByRole("button", { name: "+サブ" }).click();
  await page.getByPlaceholder("タスク名を入力").fill("子タスク");
  await page.getByRole("button", { name: "作成" }).click();

  // 「親タスク」はフォームの項目名など、画面内の別の場所にも出るので、先頭の一致で確認する
  await expect(page.getByText("親タスク", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("子タスク", { exact: true }).first()).toBeVisible();
});

// The row is the outermost div that contains both the project name and the
// given action button.
function projectRow(page: import("@playwright/test").Page, name: string) {
  // Each list row is a div.rounded-xl; names are unique so this is one row.
  return page.locator("div.rounded-xl").filter({ hasText: name });
}

test("E-6: archive hides project from sidebar and restore brings it back", async ({ page }) => {
  const name = uniqueName("Arch");
  await createProject(page, name);

  // Archive from the list page.
  await projectRow(page, name).getByRole("button", { name: "アーカイブ" }).click();
  await page.getByRole("button", { name: "アーカイブする" }).click(); // 確認ダイアログ

  // Gone from the sidebar navigation.
  await expect(page.locator("nav").getByText(name)).toHaveCount(0);

  // Show archived, then restore.
  await page.getByText("アーカイブ済みも表示").click();
  await projectRow(page, name).getByRole("button", { name: "復元" }).click();
  await page.getByRole("button", { name: "復元する" }).click(); // 確認ダイアログ

  await expect(page.locator("nav").getByText(name)).toBeVisible();
});
