import { test, expect } from "@playwright/experimental-ct-react";
import { PriorityBadge, StatusBadge, TagList, TagPill } from "./Badges";
import type { StatusDef, Tag } from "../types";

test.describe("PriorityBadge", () => {
  test("V-1a: 優先度に対応する日本語ラベルを表示する", async ({ mount }) => {
    const component = await mount(<PriorityBadge priority="URGENT" />);
    await expect(component).toHaveText("緊急");
  });

  test("V-1b: 全ての優先度がラベルに対応している", async ({ mount }) => {
    const expected = { LOW: "低", MEDIUM: "中", HIGH: "高", URGENT: "緊急" } as const;
    for (const [priority, label] of Object.entries(expected)) {
      const component = await mount(<PriorityBadge priority={priority as keyof typeof expected} />);
      await expect(component, priority).toHaveText(label);
      await component.unmount();
    }
  });
});

test.describe("StatusBadge", () => {
  const status: StatusDef = {
    id: "IN_PROGRESS",
    label: "進行中",
    color: "#6366f1",
    order: 1,
    isDone: false,
  };

  test("V-1c: ステータスのラベルを表示する", async ({ mount }) => {
    const component = await mount(<StatusBadge status={status} />);
    await expect(component).toHaveText("進行中");
  });

  test("V-1d: ステータスの色が文字色に反映される", async ({ mount }) => {
    const component = await mount(<StatusBadge status={status} />);
    // 色はデータ由来（Tailwind のクラスではない）ので、インラインスタイルで指定されている
    await expect(component).toHaveCSS("color", "rgb(99, 102, 241)");
  });
});

test.describe("TagPill", () => {
  const tag: Tag = { id: "t1", name: "backend", color: "#0ea5e9" };

  test("V-1e: タグ名を表示する（V2 と同じく # は付けない）", async ({ mount }) => {
    const component = await mount(<TagPill tag={tag} />);
    await expect(component).toContainText("backend");
    await expect(component).not.toContainText("#");
  });

  test("V-1f: onRemove 未指定なら削除ボタンを表示しない", async ({ mount }) => {
    const component = await mount(<TagPill tag={tag} />);
    await expect(component.getByRole("button")).toHaveCount(0);
  });

  test("V-1g: onRemove 指定時は削除ボタンを表示し、クリックで呼ばれる", async ({ mount }) => {
    let removed = 0;
    const component = await mount(<TagPill tag={tag} onRemove={() => (removed += 1)} />);
    await component.getByRole("button").click();
    await expect.poll(() => removed).toBe(1);
  });
});

test.describe("TagList", () => {
  const tags: Tag[] = [
    { id: "t1", name: "alphabet", color: "#0ea5e9" },
    { id: "t2", name: "b", color: "#22c55e" },
    { id: "t3", name: "gamma", color: "#a855f7" },
    { id: "t4", name: "delta", color: "#f59e0b" },
  ];

  test("V-1h: 先頭2件を4文字までで表示し、残りは「...」のピルにまとめる", async ({ mount }) => {
    const component = await mount(<TagList tags={tags} />);
    await expect(component.getByText("alph...")).toBeVisible();
    await expect(component.getByText("b", { exact: true })).toBeVisible();
    await expect(component.getByText("gamma")).toHaveCount(0);
    await expect(component.getByText("...", { exact: true })).toHaveAttribute("title", "gamma, delta");
  });

  test("V-1i: 省略したタグ名はマウスオーバー（title）で全体を確認できる", async ({ mount }) => {
    const component = await mount(<TagList tags={tags.slice(0, 1)} />);
    await expect(component.getByText("alph...")).toHaveAttribute("title", "alphabet");
    await expect(component.getByText("...", { exact: true })).toHaveCount(0);
  });
});
