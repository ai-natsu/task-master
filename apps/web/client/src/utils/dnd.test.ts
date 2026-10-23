import { describe, it, expect } from "vitest";
import { planKanbanDrag, planRowDrop } from "./dnd";
import { makeTask } from "../test/factories";

describe("planKanbanDrag", () => {
  // TODO column: t1(0), t2(1); DONE column: t3(0)
  const tasks = [
    makeTask({ id: "t1", status: "TODO", order: 0 }),
    makeTask({ id: "t2", status: "TODO", order: 1 }),
    makeTask({ id: "t3", status: "DONE", order: 0 }),
  ];

  it("C-3: same-column card→card reorders only (no status change)", () => {
    const plan = planKanbanDrag(tasks, "t2", { id: "t1", type: "card" });
    expect(plan.statusChange).toBeUndefined();
    expect(plan.reorder).toEqual([
      { id: "t2", order: 0 },
      { id: "t1", order: 1 },
    ]);
  });

  it("C-4: cross-column drop changes status and reindexes both columns", () => {
    const plan = planKanbanDrag(tasks, "t1", { id: "t3", type: "card" });
    expect(plan.statusChange).toEqual({ id: "t1", status: "DONE" });
    // t1 inserted before t3 in DONE
    expect(plan.reorder).toEqual([
      { id: "t1", order: 0 },
      { id: "t3", order: 1 },
      { id: "t2", order: 0 },
    ]);
  });

  it("C-5: dropping on empty column area appends to end", () => {
    const plan = planKanbanDrag(tasks, "t1", { id: "column:DONE", type: "column", statusId: "DONE" });
    expect(plan.statusChange).toEqual({ id: "t1", status: "DONE" });
    expect(plan.reorder?.filter((r) => r.id === "t1")[0]).toEqual({ id: "t1", order: 1 });
  });

  it("C-6: over=null is a no-op", () => {
    expect(planKanbanDrag(tasks, "t1", null)).toEqual({});
  });
});

describe("planRowDrop", () => {
  const rowTasks = () => [
    makeTask({ id: "a", parentId: null, order: 0 }),
    makeTask({ id: "b", parentId: null, order: 1 }),
    makeTask({ id: "a1", parentId: "a", order: 0 }),
    makeTask({ id: "a2", parentId: "a", order: 1 }),
    makeTask({ id: "b1", parentId: "b", order: 0 }),
  ];

  it("before a sibling under the same parent only reorders", () => {
    expect(planRowDrop(rowTasks(), "a2", "a1", "before")).toEqual({
      reorder: [
        { id: "a2", order: 0 },
        { id: "a1", order: 1 },
      ],
    });
  });

  it("returns {} when nothing changes", () => {
    expect(planRowDrop(rowTasks(), "a1", "a2", "before")).toEqual({});
    expect(planRowDrop(rowTasks(), "a1", "a1", "child")).toEqual({});
  });

  it("child makes it the last child of another parent and compacts the old siblings", () => {
    expect(planRowDrop(rowTasks(), "a1", "b", "child")).toEqual({
      reorder: [
        { id: "b1", order: 0 },
        { id: "a1", order: 1, parentId: "b" },
        { id: "a2", order: 0 },
      ],
    });
  });

  it("before a top-level row promotes a child to the top level", () => {
    expect(planRowDrop(rowTasks(), "a1", "b", "before")).toEqual({
      reorder: [
        { id: "a", order: 0 },
        { id: "a1", order: 1, parentId: null },
        { id: "b", order: 2 },
        { id: "a2", order: 0 },
      ],
    });
  });

  it("after places it below the target under the target's parent", () => {
    const plan = planRowDrop(rowTasks(), "a1", "b1", "after");
    expect(plan.reorder?.slice(0, 2)).toEqual([
      { id: "b1", order: 0 },
      { id: "a1", order: 1, parentId: "b" },
    ]);
  });

  it("rejects moving a task into its own subtree", () => {
    expect(planRowDrop(rowTasks(), "a", "a1", "child")).toEqual({});
    expect(planRowDrop(rowTasks(), "a", "a2", "after")).toEqual({});
  });
});
