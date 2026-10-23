import { describe, it, expect } from "vitest";
import { taskToFormValue } from "./TaskFormModal";
import { makeTask } from "../test/factories";

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
