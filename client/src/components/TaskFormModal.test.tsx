import { test, expect } from "@playwright/experimental-ct-react";
import { TaskFormModal, type TaskFormValue } from "./TaskFormModal";
import { mockApi } from "../test/ct";

const parentOptions = [{ id: "p-task", title: "親タスク", depth: 0 }];

test.beforeEach(async ({ page }) => {
  await mockApi(page); // ステータス・タグの一覧を固定する
});

/** フォームを開き、送信・閉じる操作の記録を返す。 */
async function setup(
  mount: Parameters<Parameters<typeof test>[2]>[0]["mount"],
  props: Partial<Parameters<typeof TaskFormModal>[0]> = {}
) {
  const submitted: TaskFormValue[] = [];
  const closed: number[] = [];
  const component = await mount(
    <TaskFormModal
      open
      mode="create"
      parentOptions={parentOptions}
      onSubmit={(v) => {
        submitted.push(v);
      }}
      onClose={() => closed.push(1)}
      {...props}
    />
  );
  return { component, submitted, closed };
}

test.describe("TaskFormModal", () => {
  test("V-4a: open=false なら何も描画しない", async ({ mount }) => {
    const component = await mount(
      <TaskFormModal open={false} mode="create" parentOptions={parentOptions} onSubmit={() => undefined} onClose={() => undefined} />
    );
    await expect(component.getByPlaceholder("タスク名を入力")).toHaveCount(0);
  });

  test("V-4b: title が空のまま送信しても onSubmit は呼ばれず、必須の赤字を表示する", async ({ mount, page }) => {
    const { submitted } = await setup(mount);
    await page.getByRole("button", { name: "作成" }).click();
    await expect(page.getByRole("alert")).toHaveText("タイトルを入力してください");
    expect(submitted).toHaveLength(0);
  });

  test("V-4c: title が空白のみでも onSubmit は呼ばれず、必須の赤字を表示する", async ({ mount, page }) => {
    const { submitted } = await setup(mount);
    await page.getByPlaceholder("タスク名を入力").fill("   ");
    await page.getByRole("button", { name: "作成" }).click();
    await expect(page.getByRole("alert")).toHaveText("タイトルを入力してください");
    expect(submitted).toHaveLength(0);
  });

  test("V-4c2: 赤字は入力し直すと消える", async ({ mount, page }) => {
    await setup(mount);
    await page.getByRole("button", { name: "作成" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await page.getByPlaceholder("タスク名を入力").pressSequentially("a");
    await expect(page.getByRole("alert")).toHaveCount(0);
  });

  test("V-4d: title があれば onSubmit が入力値付きで呼ばれる", async ({ mount, page }) => {
    const { submitted } = await setup(mount);
    await page.getByPlaceholder("タスク名を入力").fill("新しいタスク");
    await page.getByRole("button", { name: "作成" }).click();
    await expect.poll(() => submitted.length).toBe(1);
    expect(submitted[0]).toMatchObject({ title: "新しいタスク" });
  });

  test("V-4e: 開始日・期限・優先度・親タスクが送信値に含まれる", async ({ mount, page }) => {
    const { submitted } = await setup(mount);
    await page.getByPlaceholder("タスク名を入力").fill("t");

    const dates = page.locator('input[type="date"]'); // 開始日 / 期限
    await dates.nth(0).fill("2026-07-10");
    await dates.nth(1).fill("2026-07-20");

    const selects = page.locator("select");
    await selects.nth(1).selectOption("HIGH"); // 優先度
    await selects.nth(2).selectOption("p-task"); // 親タスク

    await page.getByRole("button", { name: "作成" }).click();
    await expect.poll(() => submitted.length).toBe(1);
    expect(submitted[0]).toMatchObject({
      title: "t",
      startDate: "2026-07-10",
      dueDate: "2026-07-20",
      priority: "HIGH",
      parentId: "p-task",
    });
  });

  test("V-4f: タグをクリックすると tagIds に含まれる", async ({ mount, page }) => {
    const { submitted } = await setup(mount);
    await page.getByPlaceholder("タスク名を入力").fill("t");
    await page.getByText("backend").click();
    await page.getByRole("button", { name: "作成" }).click();
    await expect.poll(() => submitted.length).toBe(1);
    expect(submitted[0]).toMatchObject({ tagIds: ["tag1"] });
  });

  test("V-4g: mode=edit ならボタンが「保存」になる", async ({ mount, page }) => {
    await setup(mount, { mode: "edit" });
    await expect(page.getByRole("button", { name: "保存" })).toBeVisible();
  });

  test("V-4h: キャンセルで onClose が呼ばれ、onSubmit は呼ばれない", async ({ mount, page }) => {
    const { submitted, closed } = await setup(mount);
    await page.getByRole("button", { name: "キャンセル" }).click();
    await expect.poll(() => closed.length).toBe(1);
    expect(submitted).toHaveLength(0);
  });

  test("V-4i: initial の値がフォームに反映される", async ({ mount, page }) => {
    await setup(mount, { initial: { title: "既存タスク", priority: "URGENT" } });
    await expect(page.getByPlaceholder("タスク名を入力")).toHaveValue("既存タスク");
  });
});
