import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import "../helpers/setup.js";
import { createApp } from "../../src/app.js";
import { prisma } from "../../src/db.js";
import { makeProject, makeTask, seedStatuses } from "../helpers/factories.js";

const app = createApp();

beforeEach(async () => {
  await seedStatuses();
});

describe("/api/projects", () => {
  it("P-1: POST creates a project with order tail+1 and archived=false", async () => {
    await makeProject({ order: 0 });
    const res = await request(app).post("/api/projects").send({ name: "New" });
    expect(res.status).toBe(201);
    expect(res.body.name).toBe("New");
    expect(res.body.archived).toBe(false);
    expect(res.body.order).toBe(1);
  });

  it("P-2: POST with empty name is 400", async () => {
    const res = await request(app).post("/api/projects").send({ name: "" });
    expect(res.status).toBe(400);
  });

  it("P-3: GET returns only non-archived, ordered, with task count", async () => {
    const a = await makeProject({ name: "A", order: 1 });
    await makeProject({ name: "Z", order: 0 });
    await makeProject({ name: "Arch", archived: true, order: 2 });
    await makeTask(a.id);

    const res = await request(app).get("/api/projects");
    expect(res.status).toBe(200);
    expect(res.body.map((p: any) => p.name)).toEqual(["Z", "A"]);
    const projA = res.body.find((p: any) => p.name === "A");
    expect(projA._count.tasks).toBe(1);
  });

  it("P-4: GET ?includeArchived=true includes archived", async () => {
    await makeProject({ name: "Live" });
    await makeProject({ name: "Arch", archived: true });
    const res = await request(app).get("/api/projects?includeArchived=true");
    expect(res.body.map((p: any) => p.name).sort()).toEqual(["Arch", "Live"]);
  });

  it("P-5/P-6: PATCH archived true then false", async () => {
    const p = await makeProject({ name: "P" });
    await request(app).patch(`/api/projects/${p.id}`).send({ archived: true });
    let list = await request(app).get("/api/projects");
    expect(list.body.find((x: any) => x.id === p.id)).toBeUndefined();

    await request(app).patch(`/api/projects/${p.id}`).send({ archived: false });
    list = await request(app).get("/api/projects");
    expect(list.body.find((x: any) => x.id === p.id)).toBeDefined();
  });

  it("P-7: PATCH nonexistent id is 404", async () => {
    const res = await request(app).patch("/api/projects/nope").send({ name: "x" });
    expect(res.status).toBe(404);
  });

  it("P-8: DELETE cascades to tasks", async () => {
    const p = await makeProject();
    await makeTask(p.id);
    const res = await request(app).delete(`/api/projects/${p.id}`);
    expect(res.status).toBe(204);
    expect(await prisma.task.count({ where: { projectId: p.id } })).toBe(0);
  });

  it("P-9: PATCH /reorder renumbers order 0..n-1", async () => {
    const a = await makeProject({ name: "A", order: 0 });
    const b = await makeProject({ name: "B", order: 1 });
    const c = await makeProject({ name: "C", order: 2 });
    const res = await request(app)
      .patch("/api/projects/reorder")
      .send({ ids: [c.id, a.id, b.id] });
    expect(res.status).toBe(200);
    const list = await request(app).get("/api/projects");
    expect(list.body.map((p: any) => p.name)).toEqual(["C", "A", "B"]);
  });
});
