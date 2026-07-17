import { test, expect } from "@playwright/test";
import { createProject, createTask, uniqueName } from "./helpers";

test("E-4: adding a status makes it available in the task form", async ({ page }) => {
  const label = uniqueName("状態");
  await page.goto("/settings");
  await page.getByPlaceholder("新しいステータス名（例: レビュー中）").fill(label);
  await page.getByRole("button", { name: "追加" }).click();
  // New status row appears (input carries the label value).
  await expect(page.locator(`input[value="${label}"]`)).toBeVisible();

  // The new status appears in the task creation form's status dropdown.
  const name = await createProject(page);
  await page.getByRole("link", { name, exact: true }).click();
  await page.getByRole("button", { name: "+ 新しいタスク" }).click();
  const statusSelect = page.locator("select").first();
  await expect(statusSelect.locator("option", { hasText: label })).toHaveCount(1);
});

test("E-5: deleting an in-use status is blocked with an error", async ({ page }) => {
  // Create a project + task (uses the default first status 未着手).
  const name = await createProject(page);
  await page.getByRole("link", { name, exact: true }).click();
  await createTask(page, uniqueName("task"));

  // First status row (未着手) is now in use → its delete must fail.
  await page.goto("/settings");
  await page.getByRole("button", { name: "削除" }).first().click();

  await expect(page.getByText(/使用中/)).toBeVisible();
  await expect(page.locator('input[value="未着手"]')).toBeVisible();
});
