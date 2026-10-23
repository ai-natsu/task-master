import { describe, it, expect } from "vitest";
import {
  projectCreateSchema,
  projectUpdateSchema,
  taskCreateSchema,
  taskReorderSchema,
  tagCreateSchema,
  statusCreateSchema,
} from "../../src/schemas.js";

// Pure unit tests: the schemas are called directly, with no HTTP, Express or
// database involved. Each limit is pinned with a pair (max passes, max+1
// fails) so the boundary's position is identified, not merely approached.
const chars = (n: number) => "a".repeat(n);
const ok = (schema: { safeParse: (v: unknown) => { success: boolean } }, value: unknown) =>
  schema.safeParse(value).success;

describe("projectCreateSchema", () => {
  it("Z-1: name 未指定は不合格", () => {
    expect(ok(projectCreateSchema, {})).toBe(false);
  });

  it("Z-2: name が空文字（下限 1 未満）は不合格", () => {
    expect(ok(projectCreateSchema, { name: "" })).toBe(false);
  });

  it("Z-3: name が 1 文字（下限ちょうど）は合格", () => {
    expect(ok(projectCreateSchema, { name: chars(1) })).toBe(true);
  });

  it("Z-4: name が 200 文字（上限ちょうど）は合格", () => {
    expect(ok(projectCreateSchema, { name: chars(200) })).toBe(true);
  });

  it("Z-5: name が 201 文字（上限超過）は不合格", () => {
    expect(ok(projectCreateSchema, { name: chars(201) })).toBe(false);
  });

  it("Z-6: name が文字列でない（数値）は不合格", () => {
    expect(ok(projectCreateSchema, { name: 123 })).toBe(false);
  });

  it("Z-7: description が 2000 文字（上限ちょうど）は合格", () => {
    expect(ok(projectCreateSchema, { name: "p", description: chars(2000) })).toBe(true);
  });

  it("Z-8: description が 2001 文字（上限超過）は不合格", () => {
    expect(ok(projectCreateSchema, { name: "p", description: chars(2001) })).toBe(false);
  });
});

describe("projectUpdateSchema", () => {
  it("Z-9: archived が真偽値でない（文字列）は不合格", () => {
    expect(ok(projectUpdateSchema, { archived: "yes" })).toBe(false);
  });

  it("Z-9b: 全項目が任意（空オブジェクト）は合格", () => {
    expect(ok(projectUpdateSchema, {})).toBe(true);
  });
});

describe("taskCreateSchema", () => {
  const base = { projectId: "p1" };

  it("Z-10: title が空文字（下限 1 未満）は不合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "" })).toBe(false);
  });

  it("Z-11: title が 300 文字（上限ちょうど）は合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: chars(300) })).toBe(true);
  });

  it("Z-12: title が 301 文字（上限超過）は不合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: chars(301) })).toBe(false);
  });

  it("Z-13: description が 5000 文字（上限ちょうど）は合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", description: chars(5000) })).toBe(true);
  });

  it("Z-14: description が 5001 文字（上限超過）は不合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", description: chars(5001) })).toBe(false);
  });

  it("Z-15: projectId 未指定（必須）は不合格", () => {
    expect(ok(taskCreateSchema, { title: "t" })).toBe(false);
  });

  it("Z-16: priority が enum 外の値は不合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", priority: "SUPER" })).toBe(false);
  });

  it("Z-17: priority が enum の各値は合格", () => {
    for (const p of ["LOW", "MEDIUM", "HIGH", "URGENT"]) {
      expect(ok(taskCreateSchema, { ...base, title: "t", priority: p }), p).toBe(true);
    }
  });

  it("Z-18: dueDate が ISO8601 でない（日付のみ）は不合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", dueDate: "2026-07-14" })).toBe(false);
  });

  it("Z-19: dueDate が null（nullable）は合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", dueDate: null })).toBe(true);
  });

  it("Z-19b: dueDate が ISO8601 の datetime は合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", dueDate: "2026-07-14T00:00:00.000Z" })).toBe(
      true
    );
  });

  it("Z-20: tagIds が配列でない（文字列）は不合格", () => {
    expect(ok(taskCreateSchema, { ...base, title: "t", tagIds: "not-an-array" })).toBe(false);
  });
});

describe("taskReorderSchema", () => {
  it("Z-21: items[].order が整数でない（小数）は不合格", () => {
    expect(ok(taskReorderSchema, { items: [{ id: "t1", order: 1.5 }] })).toBe(false);
  });

  it("Z-21b: items[].order が整数は合格", () => {
    expect(ok(taskReorderSchema, { items: [{ id: "t1", order: 0 }] })).toBe(true);
  });
});

describe("tagCreateSchema", () => {
  it("Z-22: name が空文字（下限 1 未満）は不合格", () => {
    expect(ok(tagCreateSchema, { name: "" })).toBe(false);
  });

  it("Z-23: name が 50 文字（上限ちょうど）は合格", () => {
    expect(ok(tagCreateSchema, { name: chars(50) })).toBe(true);
  });

  it("Z-24: name が 51 文字（上限超過）は不合格", () => {
    expect(ok(tagCreateSchema, { name: chars(51) })).toBe(false);
  });
});

describe("statusCreateSchema", () => {
  it("Z-25: label が空文字（下限 1 未満）は不合格", () => {
    expect(ok(statusCreateSchema, { label: "" })).toBe(false);
  });

  it("Z-26: label が 50 文字（上限ちょうど）は合格", () => {
    expect(ok(statusCreateSchema, { label: chars(50) })).toBe(true);
  });

  it("Z-27: label が 51 文字（上限超過）は不合格", () => {
    expect(ok(statusCreateSchema, { label: chars(51) })).toBe(false);
  });

  it("Z-28: isDone が真偽値でない（文字列）は不合格", () => {
    expect(ok(statusCreateSchema, { label: "s", isDone: "true" })).toBe(false);
  });
});
