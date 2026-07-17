import { describe, it, expect } from "vitest";
import { buildTaskTree, flattenWithDepth, flattenNodes, countAll } from "./tree";
import { makeTask } from "../test/factories";

describe("buildTaskTree", () => {
  it("U-1: nests children under parents, each level sorted by order", async () => {
    const tasks = [
      makeTask({ id: "a", order: 1 }),
      makeTask({ id: "b", order: 0 }),
      makeTask({ id: "a1", parentId: "a", order: 1 }),
      makeTask({ id: "a0", parentId: "a", order: 0 }),
    ];
    const tree = buildTaskTree(tasks);
    expect(tree.map((n) => n.id)).toEqual(["b", "a"]);
    const a = tree.find((n) => n.id === "a")!;
    expect(a.children.map((c) => c.id)).toEqual(["a0", "a1"]);
  });

  it("U-2: treats a task whose parent is missing from the set as a root", () => {
    const tasks = [makeTask({ id: "orphan", parentId: "gone" })];
    const tree = buildTaskTree(tasks);
    expect(tree.map((n) => n.id)).toEqual(["orphan"]);
  });

  it("U-3: empty input yields empty tree", () => {
    expect(buildTaskTree([])).toEqual([]);
  });
});

describe("flatten helpers", () => {
  const tasks = [
    makeTask({ id: "a", order: 0 }),
    makeTask({ id: "a0", parentId: "a", order: 0 }),
    makeTask({ id: "a0x", parentId: "a0", order: 0 }),
    makeTask({ id: "b", order: 1 }),
  ];
  const tree = buildTaskTree(tasks);

  it("U-4: flattenWithDepth returns DFS order with depth annotations", () => {
    expect(flattenWithDepth(tree)).toEqual([
      { id: "a", title: expect.any(String), depth: 0 },
      { id: "a0", title: expect.any(String), depth: 1 },
      { id: "a0x", title: expect.any(String), depth: 2 },
      { id: "b", title: expect.any(String), depth: 0 },
    ]);
  });

  it("U-5: flattenNodes returns {node, depth} in parent-before-child order", () => {
    const flat = flattenNodes(tree);
    expect(flat.map((f) => [f.node.id, f.depth])).toEqual([
      ["a", 0],
      ["a0", 1],
      ["a0x", 2],
      ["b", 0],
    ]);
  });

  it("U-6: countAll counts all descendants", () => {
    expect(countAll(tree)).toBe(4);
  });
});
