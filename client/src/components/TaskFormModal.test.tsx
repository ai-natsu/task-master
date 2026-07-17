import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskFormModal, taskToFormValue } from "./TaskFormModal";
import { makeTask } from "../test/factories";

vi.mock("../api/tags", () => ({
  useTags: () => ({ data: [{ id: "tag1", name: "backend", color: "#0ea5e9" }] }),
  useCreateTag: () => ({ mutateAsync: vi.fn() }),
}));

vi.mock("../api/statuses", () => ({
  useStatuses: () => ({
    data: [
      { id: "TODO", label: "未着手", color: "#64748b", order: 0, isDone: false },
      { id: "DONE", label: "完了", color: "#10b981", order: 1, isDone: true },
    ],
  }),
}));

const parentOptions = [{ id: "p-task", title: "親タスク", depth: 0 }];

function setup(props: Partial<Parameters<typeof TaskFormModal>[0]> = {}) {
  const onSubmit = vi.fn();
  const onClose = vi.fn();
  render(
    <TaskFormModal
      open
      mode="create"
      parentOptions={parentOptions}
      onSubmit={onSubmit}
      onClose={onClose}
      {...props}
    />
  );
  return { onSubmit, onClose };
}

describe("TaskFormModal", () => {
  it("V-4a: open=false なら何も描画しない", () => {
    const onSubmit = vi.fn();
    render(
      <TaskFormModal
        open={false}
        mode="create"
        parentOptions={parentOptions}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />
    );
    expect(screen.queryByPlaceholderText("タスク名を入力")).not.toBeInTheDocument();
  });

  it("V-4b: title が空のまま送信しても onSubmit は呼ばれない", async () => {
    const { onSubmit } = setup();
    await userEvent.click(screen.getByRole("button", { name: "作成" }));
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("V-4c: title が空白のみでも onSubmit は呼ばれない", async () => {
    const { onSubmit } = setup();
    await userEvent.type(screen.getByPlaceholderText("タスク名を入力"), "   ");
    await userEvent.click(screen.getByRole("button", { name: "作成" }));
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("V-4d: title があれば onSubmit が入力値付きで呼ばれる", async () => {
    const { onSubmit } = setup();
    await userEvent.type(screen.getByPlaceholderText("タスク名を入力"), "新しいタスク");
    await userEvent.click(screen.getByRole("button", { name: "作成" }));

    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ title: "新しいタスク" });
  });

  it("V-4e: 開始日・期限・優先度・親タスクが送信値に含まれる", async () => {
    const { onSubmit } = setup();
    await userEvent.type(screen.getByPlaceholderText("タスク名を入力"), "t");

    const dates = screen.getAllByDisplayValue("");
    // 開始日 / 期限（type=date）
    const dateInputs = document.querySelectorAll('input[type="date"]');
    await userEvent.type(dateInputs[0] as HTMLElement, "2026-07-10");
    await userEvent.type(dateInputs[1] as HTMLElement, "2026-07-20");

    const selects = document.querySelectorAll("select");
    await userEvent.selectOptions(selects[1] as HTMLElement, "HIGH"); // 優先度
    await userEvent.selectOptions(selects[2] as HTMLElement, "p-task"); // 親タスク

    await userEvent.click(screen.getByRole("button", { name: "作成" }));

    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      title: "t",
      startDate: "2026-07-10",
      dueDate: "2026-07-20",
      priority: "HIGH",
      parentId: "p-task",
    });
    expect(dates.length).toBeGreaterThan(0);
  });

  it("V-4f: タグをクリックすると tagIds に含まれる", async () => {
    const { onSubmit } = setup();
    await userEvent.type(screen.getByPlaceholderText("タスク名を入力"), "t");
    await userEvent.click(screen.getByText("#backend"));
    await userEvent.click(screen.getByRole("button", { name: "作成" }));

    expect(onSubmit.mock.calls[0][0]).toMatchObject({ tagIds: ["tag1"] });
  });

  it("V-4g: mode=edit ならボタンが「保存」になる", () => {
    setup({ mode: "edit" });
    expect(screen.getByRole("button", { name: "保存" })).toBeInTheDocument();
  });

  it("V-4h: キャンセルで onClose が呼ばれ、onSubmit は呼ばれない", async () => {
    const { onSubmit, onClose } = setup();
    await userEvent.click(screen.getByRole("button", { name: "キャンセル" }));
    expect(onClose).toHaveBeenCalledOnce();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("V-4i: initial の値がフォームに反映される", () => {
    setup({ initial: { title: "既存タスク", priority: "URGENT" } });
    expect(screen.getByDisplayValue("既存タスク")).toBeInTheDocument();
  });
});

describe("taskToFormValue", () => {
  it("V-4j: Task をフォーム値へ変換する（日付は YYYY-MM-DD に切り出す）", () => {
    const task = makeTask({
      title: "タスク",
      description: null,
      status: "DONE",
      priority: "HIGH",
      startDate: "2026-07-10T00:00:00.000Z",
      dueDate: "2026-07-20T00:00:00.000Z",
      parentId: "parent-1",
      tags: [{ id: "tag1", name: "backend", color: "#0ea5e9" }],
    });

    expect(taskToFormValue(task)).toEqual({
      title: "タスク",
      description: "",
      status: "DONE",
      priority: "HIGH",
      startDate: "2026-07-10",
      dueDate: "2026-07-20",
      tagIds: ["tag1"],
      parentId: "parent-1",
    });
  });

  it("V-4k: 日付が未設定なら空文字になる", () => {
    const task = makeTask({ startDate: null, dueDate: null });
    expect(taskToFormValue(task)).toMatchObject({ startDate: "", dueDate: "" });
  });

  it("V-4l: undefined を渡すと undefined を返す", () => {
    expect(taskToFormValue(undefined)).toBeUndefined();
  });
});
