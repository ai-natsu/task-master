import { test, expect } from "@playwright/experimental-ct-react";
import { ProjectFormModal, type ProjectFormValue } from "./ProjectFormModal";
import { ConfirmDialog } from "./ConfirmDialog";

test.describe("ProjectFormModal", () => {
  test("名前が空のまま送信すると onSubmit は呼ばれず、必須の赤字を表示する", async ({ mount, page }) => {
    const submitted: ProjectFormValue[] = [];
    await mount(<ProjectFormModal open mode="create" onSubmit={(v) => void submitted.push(v)} onClose={() => undefined} />);
    await page.getByRole("button", { name: "作成" }).click();
    await expect(page.getByRole("alert")).toHaveText("名前を入力してください");
    expect(submitted).toHaveLength(0);
  });

  test("名前を入力し直すと赤字が消え、送信できる", async ({ mount, page }) => {
    const submitted: ProjectFormValue[] = [];
    await mount(<ProjectFormModal open mode="create" onSubmit={(v) => void submitted.push(v)} onClose={() => undefined} />);
    await page.getByRole("button", { name: "作成" }).click();
    await page.getByPlaceholder("プロジェクト名").pressSequentially("A");
    await expect(page.getByRole("alert")).toHaveCount(0);
    await page.getByRole("button", { name: "作成" }).click();
    await expect.poll(() => submitted.length).toBe(1);
  });
});

test.describe("ConfirmDialog", () => {
  test("確定ボタンの文言と色を指定できる（アーカイブ・復元用）", async ({ mount }) => {
    const component = await mount(
      <ConfirmDialog
        open
        title="プロジェクトをアーカイブ"
        message="本当に？"
        confirmLabel="アーカイブする"
        danger={false}
        onConfirm={() => undefined}
        onCancel={() => undefined}
      />
    );
    await expect(component.getByRole("button", { name: "アーカイブする" })).toHaveClass(/bg-indigo-600/);
  });

  test("省略時は、従来どおり赤い「削除する」ボタン", async ({ mount }) => {
    const component = await mount(
      <ConfirmDialog open title="削除" message="本当に？" onConfirm={() => undefined} onCancel={() => undefined} />
    );
    await expect(component.getByRole("button", { name: "削除する" })).toHaveClass(/bg-red-600/);
  });

  test("確定・キャンセルのボタンでコールバックが呼ばれる", async ({ mount }) => {
    const events: string[] = [];
    const component = await mount(
      <ConfirmDialog
        open
        title="削除"
        message="本当に？"
        onConfirm={() => events.push("confirm")}
        onCancel={() => events.push("cancel")}
      />
    );
    await component.getByRole("button", { name: "削除する" }).click();
    await component.getByRole("button", { name: "キャンセル" }).click();
    await expect.poll(() => events).toEqual(["confirm", "cancel"]);
  });
});
