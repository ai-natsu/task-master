import { test, expect } from "@playwright/experimental-ct-react";
import { TaskFormModal, type TaskFormValue } from "./TaskFormModal";
import { ProjectFormModal, type ProjectFormValue } from "./ProjectFormModal";
import { TagSettings } from "./TagSettings";
import { HolidaySettings } from "./HolidaySettings";
import { Settings } from "../pages/Settings";
import { mockApi } from "../test/ct";

// 入力値のチェック（必須・文字数の上限）が、仕様（docs/BASIC_DESIGN.md）どおりに動くことを確認する。
// 上限: プロジェクト名 200 / 説明 2000 / タスクのタイトル 300 / 詳細 5000 / ステータス・タグ名 50 / 祝日名 100

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

const noop = () => undefined;
const parentOptions = [{ id: "p-task", title: "親タスク", depth: 0 }];

test.describe("タスクフォームの入力チェック", () => {
  test("V-5a: タイトル 300・詳細 5000・新しいタグ名 50 の上限が入力欄に設定されている", async ({ mount, page }) => {
    await mount(<TaskFormModal open mode="create" parentOptions={parentOptions} onSubmit={noop} onClose={noop} />);
    await expect(page.getByPlaceholder("タスク名を入力")).toHaveAttribute("maxlength", "300");
    await expect(page.getByPlaceholder("詳細（任意）")).toHaveAttribute("maxlength", "5000");
    await expect(page.getByPlaceholder("新しいタグ")).toHaveAttribute("maxlength", "50");
  });

  test("V-5b: タイトルは 300 文字ちょうどまで入力でき、そのまま送信できる（境界値）", async ({ mount, page }) => {
    const submitted: TaskFormValue[] = [];
    await mount(
      <TaskFormModal open mode="create" parentOptions={parentOptions} onSubmit={(v) => void submitted.push(v)} onClose={noop} />
    );
    await page.getByPlaceholder("タスク名を入力").fill("あ".repeat(300));
    await page.getByRole("button", { name: "作成" }).click();
    await expect.poll(() => submitted.length).toBe(1);
    expect(submitted[0].title).toHaveLength(300);
  });

  test("V-5c: タイトルは、キーボード入力では 301 文字目から入力できない", async ({ mount, page }) => {
    await mount(<TaskFormModal open mode="create" parentOptions={parentOptions} onSubmit={noop} onClose={noop} />);
    const title = page.getByPlaceholder("タスク名を入力");
    await title.pressSequentially("a".repeat(310));
    await expect(title).toHaveValue("a".repeat(300));
  });

  test("V-5d: 新しいタグ名が空のまま「追加」を押すと、赤字で必須を知らせる", async ({ mount, page }) => {
    await mount(<TaskFormModal open mode="create" parentOptions={parentOptions} onSubmit={noop} onClose={noop} />);
    await page.getByRole("button", { name: "追加" }).click();
    await expect(page.getByText("名前を入力してください")).toBeVisible();
  });
});

test.describe("プロジェクトフォームの入力チェック", () => {
  test("V-5e: 名前 200・説明 2000 の上限が入力欄に設定されている", async ({ mount, page }) => {
    await mount(<ProjectFormModal open mode="create" onSubmit={noop} onClose={noop} />);
    await expect(page.getByPlaceholder("プロジェクト名")).toHaveAttribute("maxlength", "200");
    await expect(page.getByPlaceholder("説明（任意）")).toHaveAttribute("maxlength", "2000");
  });

  test("V-5f: 名前は 200 文字ちょうどまで入力でき、そのまま送信できる（境界値）", async ({ mount, page }) => {
    const submitted: ProjectFormValue[] = [];
    await mount(<ProjectFormModal open mode="create" onSubmit={(v) => void submitted.push(v)} onClose={noop} />);
    await page.getByPlaceholder("プロジェクト名").fill("あ".repeat(200));
    await page.getByRole("button", { name: "作成" }).click();
    await expect.poll(() => submitted.length).toBe(1);
    expect(submitted[0].name).toHaveLength(200);
  });

  test("V-5g: 名前は、キーボード入力では 201 文字目から入力できない", async ({ mount, page }) => {
    await mount(<ProjectFormModal open mode="create" onSubmit={noop} onClose={noop} />);
    const name = page.getByPlaceholder("プロジェクト名");
    await name.pressSequentially("b".repeat(210));
    await expect(name).toHaveValue("b".repeat(200));
  });

  test("V-5h: 名前が空白だけの場合も、必須の赤字を表示して送信しない", async ({ mount, page }) => {
    const submitted: ProjectFormValue[] = [];
    await mount(<ProjectFormModal open mode="create" onSubmit={(v) => void submitted.push(v)} onClose={noop} />);
    await page.getByPlaceholder("プロジェクト名").fill("   ");
    await page.getByRole("button", { name: "作成" }).click();
    await expect(page.getByRole("alert")).toHaveText("名前を入力してください");
    expect(submitted).toHaveLength(0);
  });
});

test.describe("設定画面の入力チェック", () => {
  test("V-5i: タグ名の上限（50）と、空のまま追加したときの赤字", async ({ mount }) => {
    const component = await mount(<TagSettings />);
    const input = component.getByPlaceholder("新しいタグ名");
    await expect(input).toHaveAttribute("maxlength", "50");
    await input.pressSequentially("c".repeat(60));
    await expect(input).toHaveValue("c".repeat(50));

    await input.fill("");
    await component.getByRole("button", { name: "追加" }).click();
    await expect(component.getByRole("alert")).toHaveText("名前を入力してください");
  });

  test("V-5j: 祝日名の上限（100）と、名称・日付が空のまま追加したときの赤字", async ({ mount }) => {
    const component = await mount(<HolidaySettings />);
    const name = component.getByPlaceholder("新しい祝日名");
    await expect(name).toHaveAttribute("maxlength", "100");
    await name.pressSequentially("d".repeat(110));
    await expect(name).toHaveValue("d".repeat(100));

    await name.fill("");
    await component.getByRole("button", { name: "追加" }).click();
    await expect(component.getByRole("alert")).toHaveText("名称を入力してください");

    await name.fill("祝日");
    await component.getByLabel("日付").fill("");
    await component.getByRole("button", { name: "追加" }).click();
    await expect(component.getByRole("alert")).toHaveText("日付を入力してください");
  });

  test("V-5k: ステータス名の上限（50）と、空のまま追加したときの赤字", async ({ mount }) => {
    const component = await mount(<Settings />);
    const input = component.getByPlaceholder("新しいステータス名（例: レビュー中）");
    await expect(input).toHaveAttribute("maxlength", "50");
    await input.pressSequentially("e".repeat(60));
    await expect(input).toHaveValue("e".repeat(50));

    await input.fill("");
    await component
      .locator("section")
      .filter({ hasText: "ステータス設定" })
      .getByRole("button", { name: "追加" })
      .click();
    await expect(component.getByRole("alert").first()).toHaveText("名前を入力してください");
  });
});
