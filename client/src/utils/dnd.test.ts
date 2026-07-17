import { describe, it, expect } from "vitest";
import { planKanbanDrag, planTreeDrag } from "./dnd";
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

describe("planTreeDrag", () => {
  const tasks = [
    makeTask({ id: "a", parentId: null, order: 0 }),
    makeTask({ id: "b", parentId: null, order: 1 }),
    makeTask({ id: "c1", parentId: "a", order: 0 }),
  ];

  it("C-1: reorders within the same parent group", () => {
    const plan = planTreeDrag(tasks, "b", "a");
    expect(plan.reorder).toEqual([
      { id: "b", order: 0 },
      { id: "a", order: 1 },
    ]);
  });

  it("C-2: cross-parent drag is a no-op", () => {
    const plan = planTreeDrag(tasks, "c1", "b");
    expect(plan).toEqual({});
  });

  it("C-2b: dropping on itself is a no-op", () => {
    expect(planTreeDrag(tasks, "a", "a")).toEqual({});
  });
});
