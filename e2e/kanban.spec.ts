import { test, expect, type Page, type Locator } from "@playwright/test";
import { createProject, createTask, uniqueName } from "./helpers";

// dnd-kit's PointerSensor needs intermediate pointermove events; Playwright's
// dragTo can be too abrupt, so drive the pointer manually in small steps.
async function dragTo(page: Page, source: Locator, target: Locator) {
  const s = await source.boundingBox();
  const t = await target.boundingBox();
  if (!s || !t) throw new Error("missing bounding box");
  const sx = s.x + s.width / 2;
  const sy = s.y + s.height / 2;
  const tx = t.x + t.width / 2;
  const ty = t.y + 20;

  await page.mouse.move(sx, sy);
  await page.mouse.down();
  for (let i = 1; i <= 8; i++) {
    await page.mouse.move(sx + ((tx - sx) * i) / 8, sy + ((ty - sy) * i) / 8);
    await page.waitForTimeout(30);
  }
  await page.mouse.up();
}

test("E-2: dragging a card to another column changes status and persists", async ({ page }) => {
  const name = await createProject(page);
  await page.getByRole("link", { name, exact: true }).click();
  const title = uniqueName("card");
  await createTask(page, title);

  await page.getByRole("button", { name: "カンバン" }).click();

  const card = page.getByText(title, { exact: true });
  const doneColumn = page.getByTestId("kanban-col-DONE");

  await dragTo(page, card, doneColumn);

  // The card now lives in the 完了 column.
  await expect(doneColumn.getByText(title, { exact: true })).toBeVisible();

  // Persisted across reload.
  await page.reload();
  await page.getByRole("button", { name: "カンバン" }).click();
  await expect(page.getByTestId("kanban-col-DONE").getByText(title, { exact: true })).toBeVisible();
});
