import { test, expect } from "@playwright/experimental-ct-react";
import { StatsCards } from "./StatsCards";
import { mockApi } from "../test/ct";
import type { Stats } from "../types";

const stats: Stats = {
  total: 10,
  byStatus: { TODO: 6, DONE: 4 },
  byPriority: { LOW: 1, MEDIUM: 2, HIGH: 3, URGENT: 4 },
  overdue: 2,
  dueSoon: 1,
  completedLast7Days: 4,
  completionRate: 40,
};

test.beforeEach(async ({ page }) => {
  await mockApi(page); // ステータスの一覧を固定する
});

test.describe("StatsCards", () => {
  test("V-2: 優先度の行を、緊急→高→中→低の順に表示する", async ({ mount }) => {
    const component = await mount(<StatsCards stats={stats} />);
    const labels = await component.getByText("優先度別").evaluate((title) => {
      const card = title.closest("div");
      // 子要素を持たない span（バッジの文字）だけを数える
      return Array.from(card?.querySelectorAll("span") ?? [])
        .filter((s) => s.children.length === 0)
        .map((s) => s.textContent ?? "")
        .filter((t) => ["緊急", "高", "中", "低"].includes(t));
    });
    expect(labels).toEqual(["緊急", "高", "中", "低"]);
  });

  test("V-2b: 完了率とタスク総数を表示する", async ({ mount }) => {
    const component = await mount(<StatsCards stats={stats} />);
    await expect(component.getByText("40%")).toBeVisible();
    await expect(component.getByText("タスク総数")).toBeVisible();
  });
});
