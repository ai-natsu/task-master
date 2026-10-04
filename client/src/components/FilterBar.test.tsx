import { test, expect } from "@playwright/experimental-ct-react";
import { FilterBar, type FilterState } from "./FilterBar";
import { mockApi } from "../test/ct";
import type { Tag } from "../types";

const tags: Tag[] = [
  { id: "tag1", name: "backend", color: "#0ea5e9" },
  { id: "tag2", name: "design", color: "#8b5cf6" },
];

const empty: FilterState = { search: "" };

test.beforeEach(async ({ page }) => {
  await mockApi(page); // ステータスの選択肢を固定する
});

test.describe("FilterBar", () => {
  test("V-3a: ステータス選択で onChange が status 付きで発火する", async ({ mount }) => {
    const calls: FilterState[] = [];
    const component = await mount(<FilterBar value={empty} onChange={(v) => calls.push(v)} tags={tags} />);
    await component.locator("select").nth(0).selectOption("DONE");
    await expect.poll(() => calls).toContainEqual({ search: "", status: "DONE" });
  });

  test("V-3b: 優先度選択で onChange が priority 付きで発火する", async ({ mount }) => {
    const calls: FilterState[] = [];
    const component = await mount(<FilterBar value={empty} onChange={(v) => calls.push(v)} tags={tags} />);
    await component.locator("select").nth(1).selectOption("HIGH");
    await expect.poll(() => calls).toContainEqual({ search: "", priority: "HIGH" });
  });

  test("V-3c: タグ選択で onChange が tagId 付きで発火する", async ({ mount }) => {
    const calls: FilterState[] = [];
    const component = await mount(<FilterBar value={empty} onChange={(v) => calls.push(v)} tags={tags} />);
    await component.locator("select").nth(2).selectOption("tag1");
    await expect.poll(() => calls).toContainEqual({ search: "", tagId: "tag1" });
  });

  test("V-3d: 検索入力で onChange が search 付きで発火する", async ({ mount }) => {
    const calls: FilterState[] = [];
    const component = await mount(<FilterBar value={empty} onChange={(v) => calls.push(v)} tags={tags} />);
    await component.getByPlaceholder("タスクを検索...").fill("a");
    await expect.poll(() => calls).toContainEqual({ search: "a" });
  });

  test("V-3e: 「すべて」を選び直すと該当キーが undefined になる", async ({ mount }) => {
    const calls: FilterState[] = [];
    const component = await mount(
      <FilterBar value={{ search: "", status: "DONE" }} onChange={(v) => calls.push(v)} tags={tags} />
    );
    await component.locator("select").nth(0).selectOption("");
    await expect.poll(() => calls.length).toBeGreaterThan(0);
    expect(calls[0].status).toBeUndefined();
    expect(calls[0].search).toBe("");
  });

  test("V-3f: フィルタ未指定なら「クリア」を表示しない", async ({ mount }) => {
    const component = await mount(<FilterBar value={empty} onChange={() => undefined} tags={tags} />);
    await expect(component.getByText("クリア")).toHaveCount(0);
  });

  test("V-3g: フィルタ指定時は「クリア」を表示し、押すと全条件がリセットされる", async ({ mount }) => {
    const calls: FilterState[] = [];
    const component = await mount(
      <FilterBar
        value={{ search: "x", status: "DONE", priority: "HIGH", tagId: "tag1" }}
        onChange={(v) => calls.push(v)}
        tags={tags}
      />
    );
    await component.getByText("クリア").click();
    await expect.poll(() => calls).toContainEqual({ search: "" });
  });
});
