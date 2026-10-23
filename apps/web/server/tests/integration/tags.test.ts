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

describe("/api/tags", () => {
  it("G-1: POST creates a tag", async () => {
    const res = await request(app).post("/api/tags").send({ name: "backend" });
    expect(res.status).toBe(201);
    expect(res.body.name).toBe("backend");
  });

  it("G-2: POST duplicate name is 409", async () => {
    await request(app).post("/api/tags").send({ name: "dup" });
    const res = await request(app).post("/api/tags").send({ name: "dup" });
    expect(res.status).toBe(409);
  });

  it("G-3: DELETE removes tag and detaches from tasks", async () => {
    const tag = await prisma.tag.create({ data: { name: "temp" } });
    const p = await makeProject();
    const t = await makeTask(p.id);
    await prisma.taskTag.create({ data: { taskId: t.id, tagId: tag.id } });

    const res = await request(app).delete(`/api/tags/${tag.id}`);
    expect(res.status).toBe(204);
    expect(await prisma.taskTag.count({ where: { tagId: tag.id } })).toBe(0);
  });
});
