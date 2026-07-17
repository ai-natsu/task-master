import { type Page, expect } from "@playwright/test";

let seq = 0;
export function uniqueName(prefix = "E2E") {
  seq += 1;
  return `${prefix}-${Date.now()}-${seq}`;
}

/** Create a project via the projects list page and open it. Returns its name. */
export async function createProject(page: Page, name = uniqueName()) {
  await page.goto("/projects");
  await page.getByRole("button", { name: "+ 新しいプロジェクト" }).click();
  await page.getByPlaceholder("プロジェクト名").fill(name);
  await page.getByRole("button", { name: "作成" }).click();
  // The list-page link has the exact name; the sidebar link includes a task count.
  await expect(page.getByRole("link", { name, exact: true })).toBeVisible();
  return name;
}

/** From a project detail page, create a top-level task. */
export async function createTask(page: Page, title: string) {
  await page.getByRole("button", { name: "+ 新しいタスク" }).click();
  await page.getByPlaceholder("タスク名を入力").fill(title);
  await page.getByRole("button", { name: "作成" }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
}
