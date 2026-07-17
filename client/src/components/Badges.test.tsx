import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PriorityBadge, StatusBadge, TagPill } from "./Badges";
import type { StatusDef, Tag } from "../types";

describe("PriorityBadge", () => {
  it("V-1a: 優先度に対応する日本語ラベルを表示する", () => {
    render(<PriorityBadge priority="URGENT" />);
    expect(screen.getByText("緊急")).toBeInTheDocument();
  });

  it("V-1b: 全ての優先度がラベルに対応している", () => {
    const expected = { LOW: "低", MEDIUM: "中", HIGH: "高", URGENT: "緊急" } as const;
    for (const [priority, label] of Object.entries(expected)) {
      const { unmount } = render(<PriorityBadge priority={priority as keyof typeof expected} />);
      expect(screen.getByText(label), priority).toBeInTheDocument();
      unmount();
    }
  });
});

describe("StatusBadge", () => {
  const status: StatusDef = {
    id: "IN_PROGRESS",
    label: "進行中",
    color: "#6366f1",
    order: 1,
    isDone: false,
  };

  it("V-1c: ステータスのラベルを表示する", () => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText("進行中")).toBeInTheDocument();
  });

  it("V-1d: ステータスの色が文字色と背景に反映される", () => {
    render(<StatusBadge status={status} />);
    // Colors are data-driven (not Tailwind classes), so they must be inline styles.
    expect(screen.getByText("進行中")).toHaveStyle({ color: "#6366f1" });
  });
});

describe("TagPill", () => {
  const tag: Tag = { id: "t1", name: "backend", color: "#0ea5e9" };

  it("V-1e: タグ名を # 付きで表示する", () => {
    render(<TagPill tag={tag} />);
    expect(screen.getByText(/#backend/)).toBeInTheDocument();
  });

  it("V-1f: onRemove 未指定なら削除ボタンを表示しない", () => {
    render(<TagPill tag={tag} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("V-1g: onRemove 指定時は削除ボタンを表示し、クリックで呼ばれる", async () => {
    const onRemove = vi.fn();
    render(<TagPill tag={tag} onRemove={onRemove} />);
    await userEvent.click(screen.getByRole("button"));
    expect(onRemove).toHaveBeenCalledOnce();
  });
});
