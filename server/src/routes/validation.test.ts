import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import { createApp } from "../app.js";
import { makeProject, makeTask, seedStatuses } from "../test/factories.js";

const app = createApp();

// Boundary-value tests aimed squarely at the zod schemas defined in each
// router. Other suites only touch validation incidentally (one "empty name"
// case), so limits and type coercion are verified here instead.
const chars = (n: number) => "a".repeat(n);

let projectId: string;

beforeEach(async () => {
  await seedStatuses();
  const p = await makeProject();
  projectId = p.id;
});

describe("zod validation: POST /api/projects", () => {
  it("Z-1: body.name 未指定 → 400", async () => {
    const res = await request(app).post("/api/projects").send({});
    expect(res.status).toBe(400);
  });

  it("Z-2: body.name が空文字（下限 1 未満） → 400", async () => {
    const res = await request(app).post("/api/projects").send({ name: "" });
    expect(res.status).toBe(400);
  });

  it("Z-3: body.name が 1 文字（下限ちょうど） → 201", async () => {
    const res = await request(app).post("/api/projects").send({ name: chars(1) });
    expect(res.status).toBe(201);
  });

  it("Z-4: body.name が 200 文字（上限ちょうど） → 201", async () => {
    const res = await request(app).post("/api/projects").send({ name: chars(200) });
    expect(res.status).toBe(201);
  });

  it("Z-5: body.name が 201 文字（上限超過） → 400", async () => {
    const res = await request(app).post("/api/projects").send({ name: chars(201) });
    expect(res.status).toBe(400);
  });

  it("Z-6: body.name が文字列でない（数値） → 400", async () => {
    const res = await request(app).post("/api/projects").send({ name: 123 });
    expect(res.status).toBe(400);
  });

  it("Z-7: body.description が 2000 文字（上限ちょうど） → 201", async () => {
    const res = await request(app)
      .post("/api/projects")
      .send({ name: "p", description: chars(2000) });
    expect(res.status).toBe(201);
  });

  it("Z-8: body.description が 2001 文字（上限超過） → 400", async () => {
    const res = await request(app)
      .post("/api/projects")
      .send({ name: "p", description: chars(2001) });
    expect(res.status).toBe(400);
  });
});

describe("zod validation: PATCH /api/projects/:id", () => {
  it("Z-9: body.archived が真偽値でない（文字列） → 400", async () => {
    const res = await request(app).patch(`/api/projects/${projectId}`).send({ archived: "yes" });
    expect(res.status).toBe(400);
  });
});

describe("zod validation: POST /api/tasks", () => {
  it("Z-10: body.title が空文字（下限 1 未満） → 400", async () => {
    const res = await request(app).post("/api/tasks").send({ title: "", projectId });
    expect(res.status).toBe(400);
  });

  it("Z-11: body.title が 300 文字（上限ちょうど） → 201", async () => {
    const res = await request(app).post("/api/tasks").send({ title: chars(300), projectId });
    expect(res.status).toBe(201);
  });

  it("Z-12: body.title が 301 文字（上限超過） → 400", async () => {
    const res = await request(app).post("/api/tasks").send({ title: chars(301), projectId });
    expect(res.status).toBe(400);
  });

  it("Z-13: body.description が 5000 文字（上限ちょうど） → 201", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId, description: chars(5000) });
    expect(res.status).toBe(201);
  });

  it("Z-14: body.description が 5001 文字（上限超過） → 400", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId, description: chars(5001) });
    expect(res.status).toBe(400);
  });

  it("Z-15: body.projectId 未指定（必須） → 400", async () => {
    const res = await request(app).post("/api/tasks").send({ title: "t" });
    expect(res.status).toBe(400);
  });

  it("Z-16: body.priority が許可外の値 → 400", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId, priority: "SUPER" });
    expect(res.status).toBe(400);
  });

  it("Z-17: body.priority が許可値 URGENT → 201", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId, priority: "URGENT" });
    expect(res.status).toBe(201);
  });

  it("Z-18: body.dueDate が ISO8601 形式でない（日付のみ） → 400", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId, dueDate: "2026-07-14" });
    expect(res.status).toBe(400);
  });

  it("Z-19: body.dueDate が null（許容） → 201", async () => {
    const res = await request(app).post("/api/tasks").send({ title: "t", projectId, dueDate: null });
    expect(res.status).toBe(201);
  });

  it("Z-20: body.tagIds が配列でない（文字列） → 400", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId, tagIds: "not-an-array" });
    expect(res.status).toBe(400);
  });
});

describe("zod validation: PATCH /api/tasks/reorder", () => {
  it("Z-21: items[].order が整数でない（小数） → 400", async () => {
    const t = await makeTask(projectId);
    const res = await request(app)
      .patch("/api/tasks/reorder")
      .send({ items: [{ id: t.id, order: 1.5 }] });
    expect(res.status).toBe(400);
  });
});

describe("zod validation: POST /api/tags", () => {
  it("Z-22: body.name が空文字（下限 1 未満） → 400", async () => {
    const res = await request(app).post("/api/tags").send({ name: "" });
    expect(res.status).toBe(400);
  });

  it("Z-23: body.name が 50 文字（上限ちょうど） → 201", async () => {
    const res = await request(app).post("/api/tags").send({ name: chars(50) });
    expect(res.status).toBe(201);
  });

  it("Z-24: body.name が 51 文字（上限超過） → 400", async () => {
    const res = await request(app).post("/api/tags").send({ name: chars(51) });
    expect(res.status).toBe(400);
  });
});

describe("zod validation: POST /api/statuses", () => {
  it("Z-25: body.label が空文字（下限 1 未満） → 400", async () => {
    const res = await request(app).post("/api/statuses").send({ label: "" });
    expect(res.status).toBe(400);
  });

  it("Z-26: body.label が 50 文字（上限ちょうど） → 201", async () => {
    const res = await request(app).post("/api/statuses").send({ label: chars(50) });
    expect(res.status).toBe(201);
  });

  it("Z-27: body.label が 51 文字（上限超過） → 400", async () => {
    const res = await request(app).post("/api/statuses").send({ label: chars(51) });
    expect(res.status).toBe(400);
  });

  it("Z-28: body.isDone が真偽値でない（文字列） → 400", async () => {
    const res = await request(app).post("/api/statuses").send({ label: "s", isDone: "true" });
    expect(res.status).toBe(400);
  });
});
