import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import "../test/setup.js";
import { createApp } from "../app.js";
import { prisma } from "../db.js";
import { makeProject, makeTask, seedStatuses } from "../test/factories.js";

const app = createApp();

let projectId: string;

beforeEach(async () => {
  await seedStatuses();
  const p = await makeProject();
  projectId = p.id;
});

describe("/api/tasks", () => {
  it("T-1: POST creates a task, tags serialized to array, order tail+1", async () => {
    await makeTask(projectId, { order: 0 });
    const res = await request(app).post("/api/tasks").send({ title: "New", projectId });
    expect(res.status).toBe(201);
    expect(res.body.order).toBe(1);
    expect(Array.isArray(res.body.tags)).toBe(true);
  });

  it("T-2: POST without status adopts first status (min order)", async () => {
    const res = await request(app).post("/api/tasks").send({ title: "X", projectId });
    expect(res.body.status).toBe("TODO");
  });

  it("T-3: POST with invalid status is 400", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "X", projectId, status: "GHOST" });
    expect(res.status).toBe(400);
  });

  it("T-4: POST with nonexistent parentId is 400", async () => {
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "X", projectId, parentId: "nope" });
    expect(res.status).toBe(400);
  });

  it("T-5: POST with tagIds attaches tags", async () => {
    const tag = await prisma.tag.create({ data: { name: "urgent" } });
    const res = await request(app)
      .post("/api/tasks")
      .send({ title: "X", projectId, tagIds: [tag.id] });
    expect(res.body.tags.map((t: any) => t.name)).toEqual(["urgent"]);
  });

  it("T-6: GET without projectId excludes archived projects' tasks", async () => {
    await makeTask(projectId, { title: "Live" });
    const arch = await makeProject({ archived: true });
    await makeTask(arch.id, { title: "Hidden" });
    const res = await request(app).get("/api/tasks");
    const titles = res.body.map((t: any) => t.title);
    expect(titles).toContain("Live");
    expect(titles).not.toContain("Hidden");
  });

  it("T-7: GET filters combine (status + priority)", async () => {
    await makeTask(projectId, { title: "match", status: "DONE", priority: "HIGH" });
    await makeTask(projectId, { title: "miss1", status: "TODO", priority: "HIGH" });
    await makeTask(projectId, { title: "miss2", status: "DONE", priority: "LOW" });
    const res = await request(app).get(`/api/tasks?status=DONE&priority=HIGH`);
    expect(res.body.map((t: any) => t.title)).toEqual(["match"]);
  });

  it("T-8: GET ?parentId=null returns only top-level", async () => {
    const parent = await makeTask(projectId, { title: "parent" });
    await makeTask(projectId, { title: "child", parentId: parent.id });
    const res = await request(app).get(`/api/tasks?projectId=${projectId}&parentId=null`);
    expect(res.body.map((t: any) => t.title)).toEqual(["parent"]);
  });

  it("T-9: GET ?search matches title or description", async () => {
    await makeTask(projectId, { title: "alpha" });
    await makeTask(projectId, { title: "beta" });
    const res = await request(app).get(`/api/tasks?search=alph`);
    expect(res.body.map((t: any) => t.title)).toEqual(["alpha"]);
  });

  it("T-10/T-11: PATCH status valid then invalid", async () => {
    const t = await makeTask(projectId);
    const ok = await request(app).patch(`/api/tasks/${t.id}`).send({ status: "DONE" });
    expect(ok.status).toBe(200);
    expect(ok.body.status).toBe("DONE");
    const bad = await request(app).patch(`/api/tasks/${t.id}`).send({ status: "GHOST" });
    expect(bad.status).toBe(400);
  });

  it("T-12: PATCH tagIds replaces existing tags", async () => {
    const tag1 = await prisma.tag.create({ data: { name: "a" } });
    const tag2 = await prisma.tag.create({ data: { name: "b" } });
    const t = await makeTask(projectId);
    await request(app).patch(`/api/tasks/${t.id}`).send({ tagIds: [tag1.id] });
    const res = await request(app).patch(`/api/tasks/${t.id}`).send({ tagIds: [tag2.id] });
    expect(res.body.tags.map((x: any) => x.name)).toEqual(["b"]);
  });

  it("T-13: DELETE parent cascades to descendants", async () => {
    const parent = await makeTask(projectId);
    const child = await makeTask(projectId, { parentId: parent.id });
    await request(app).delete(`/api/tasks/${parent.id}`);
    expect(await prisma.task.findUnique({ where: { id: child.id } })).toBeNull();
  });

  it("T-14: PATCH /reorder applies order in one batch", async () => {
    const a = await makeTask(projectId, { title: "A", order: 0 });
    const b = await makeTask(projectId, { title: "B", order: 1 });
    await request(app)
      .patch("/api/tasks/reorder")
      .send({ items: [{ id: b.id, order: 0 }, { id: a.id, order: 1 }] });
    const res = await request(app).get(`/api/tasks?projectId=${projectId}`);
    expect(res.body.map((t: any) => t.title)).toEqual(["B", "A"]);
  });

  it("T-15: PATCH /reorder can reparent (parentId) in the same batch", async () => {
    const a = await makeTask(projectId, { title: "A", order: 0 });
    const b = await makeTask(projectId, { title: "B", order: 1 });
    const res = await request(app)
      .patch("/api/tasks/reorder")
      .send({ items: [{ id: b.id, order: 0, parentId: a.id }] });
    expect(res.status).toBe(200);
    expect((await prisma.task.findUnique({ where: { id: b.id } }))?.parentId).toBe(a.id);
  });

  it("T-16: PATCH /reorder rejects moving a task under its own subtask (400, nothing written)", async () => {
    const a = await makeTask(projectId, { title: "A", order: 0 });
    const b = await makeTask(projectId, { title: "B", parentId: a.id, order: 0 });
    const res = await request(app)
      .patch("/api/tasks/reorder")
      .send({ items: [{ id: a.id, order: 5, parentId: b.id }] });
    expect(res.status).toBe(400);
    const unchanged = await prisma.task.findUnique({ where: { id: a.id } });
    expect(unchanged?.parentId).toBeNull();
    expect(unchanged?.order).toBe(0);
  });
});

describe("/api/tasks/:id/move (cycle detection)", () => {
  // Build A > B > C and a separate D
  async function buildTree() {
    const a = await makeTask(projectId, { title: "A" });
    const b = await makeTask(projectId, { title: "B", parentId: a.id });
    const c = await makeTask(projectId, { title: "C", parentId: b.id });
    const d = await makeTask(projectId, { title: "D" });
    return { a, b, c, d };
  }

  it("M-1: moving C under B (valid) is 200", async () => {
    const { b, c } = await buildTree();
    const res = await request(app).patch(`/api/tasks/${c.id}/move`).send({ parentId: b.id });
    expect(res.status).toBe(200);
  });

  it("M-2: moving A under itself is 400", async () => {
    const { a } = await buildTree();
    const res = await request(app).patch(`/api/tasks/${a.id}/move`).send({ parentId: a.id });
    expect(res.status).toBe(400);
  });

  it("M-3: moving A under its own grandchild C is 400", async () => {
    const { a, c } = await buildTree();
    const res = await request(app).patch(`/api/tasks/${a.id}/move`).send({ parentId: c.id });
    expect(res.status).toBe(400);
  });

  it("M-4: moving A under unrelated D is 200", async () => {
    const { a, d } = await buildTree();
    const res = await request(app).patch(`/api/tasks/${a.id}/move`).send({ parentId: d.id });
    expect(res.status).toBe(200);
  });

  it("M-5: moving to top-level (parentId=null) is 200", async () => {
    const { c } = await buildTree();
    const res = await request(app).patch(`/api/tasks/${c.id}/move`).send({ parentId: null });
    expect(res.status).toBe(200);
    const updated = await prisma.task.findUnique({ where: { id: c.id } });
    expect(updated?.parentId).toBeNull();
  });
});
