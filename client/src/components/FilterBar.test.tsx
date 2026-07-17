import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FilterBar, type FilterState } from "./FilterBar";
import type { Tag } from "../types";

// Statuses come from the server; mock the hook so the dropdown has known options.
vi.mock("../api/statuses", () => ({
  useStatuses: () => ({
    data: [
      { id: "TODO", label: "未着手", color: "#64748b", order: 0, isDone: false },
      { id: "DONE", label: "完了", color: "#10b981", order: 1, isDone: true },
    ],
  }),
}));

const tags: Tag[] = [
  { id: "tag1", name: "backend", color: "#0ea5e9" },
  { id: "tag2", name: "design", color: "#8b5cf6" },
];

const empty: FilterState = { search: "" };

describe("FilterBar", () => {
  it("V-3a: ステータス選択で onChange が status 付きで発火する", async () => {
    const onChange = vi.fn();
    render(<FilterBar value={empty} onChange={onChange} tags={tags} />);

    await userEvent.selectOptions(screen.getByDisplayValue("すべてのステータス"), "DONE");

    expect(onChange).toHaveBeenCalledWith({ search: "", status: "DONE" });
  });

  it("V-3b: 優先度選択で onChange が priority 付きで発火する", async () => {
    const onChange = vi.fn();
    render(<FilterBar value={empty} onChange={onChange} tags={tags} />);

    await userEvent.selectOptions(screen.getByDisplayValue("すべての優先度"), "HIGH");

    expect(onChange).toHaveBeenCalledWith({ search: "", priority: "HIGH" });
  });

  it("V-3c: タグ選択で onChange が tagId 付きで発火する", async () => {
    const onChange = vi.fn();
    render(<FilterBar value={empty} onChange={onChange} tags={tags} />);

    await userEvent.selectOptions(screen.getByDisplayValue("すべてのタグ"), "tag1");

    expect(onChange).toHaveBeenCalledWith({ search: "", tagId: "tag1" });
  });

  it("V-3d: 検索入力で onChange が search 付きで発火する", async () => {
    const onChange = vi.fn();
    render(<FilterBar value={empty} onChange={onChange} tags={tags} />);

    await userEvent.type(screen.getByPlaceholderText("タスクを検索..."), "a");

    expect(onChange).toHaveBeenCalledWith({ search: "a" });
  });

  it('V-3e: 「すべて」を選び直すと該当キーが undefined になる', async () => {
    const onChange = vi.fn();
    render(<FilterBar value={{ search: "", status: "DONE" }} onChange={onChange} tags={tags} />);

    await userEvent.selectOptions(screen.getByDisplayValue("完了"), "");

    expect(onChange).toHaveBeenCalledWith({ search: "", status: undefined });
  });

  it("V-3f: フィルタ未指定なら「クリア」を表示しない", () => {
    render(<FilterBar value={empty} onChange={vi.fn()} tags={tags} />);
    expect(screen.queryByText("クリア")).not.toBeInTheDocument();
  });

  it("V-3g: フィルタ指定時は「クリア」を表示し、押すと全条件がリセットされる", async () => {
    const onChange = vi.fn();
    render(
      <FilterBar
        value={{ search: "x", status: "DONE", priority: "HIGH", tagId: "tag1" }}
        onChange={onChange}
        tags={tags}
      />
    );

    await userEvent.click(screen.getByText("クリア"));

    expect(onChange).toHaveBeenCalledWith({ search: "" });
  });
});
