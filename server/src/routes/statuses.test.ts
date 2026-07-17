import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import "../test/setup.js";
import { createApp } from "../app.js";
import { makeProject, makeTask, seedStatuses } from "../test/factories.js";

const app = createApp();

beforeEach(async () => {
  await seedStatuses();
});

describe("/api/statuses", () => {
  it("S-1: GET returns statuses ordered by order", async () => {
    const res = await request(app).get("/api/statuses");
    expect(res.body.map((s: any) => s.id)).toEqual(["TODO", "IN_PROGRESS", "DONE"]);
  });

  it("S-2: POST creates status with order tail+1", async () => {
    const res = await request(app).post("/api/statuses").send({ label: "レビュー中" });
    expect(res.status).toBe(201);
    expect(res.body.order).toBe(3);
  });

  it("S-3: PATCH updates label/color/isDone", async () => {
    const res = await request(app)
      .patch("/api/statuses/IN_PROGRESS")
      .send({ label: "作業中", isDone: true });
    expect(res.body.label).toBe("作業中");
    expect(res.body.isDone).toBe(true);
  });

  it("S-4: PATCH /reorder renumbers", async () => {
    await request(app)
      .patch("/api/statuses/reorder")
      .send({ ids: ["DONE", "TODO", "IN_PROGRESS"] });
    const res = await request(app).get("/api/statuses");
    expect(res.body.map((s: any) => s.id)).toEqual(["DONE", "TODO", "IN_PROGRESS"]);
  });

  it("S-5: DELETE status in use is 409 with count", async () => {
    const p = await makeProject();
    await makeTask(p.id, { status: "TODO" });
    await makeTask(p.id, { status: "TODO" });
    const res = await request(app).delete("/api/statuses/TODO");
    expect(res.status).toBe(409);
    expect(res.body.error).toContain("2");
  });

  it("S-7: DELETE unused status (multiple exist) is 204", async () => {
    const res = await request(app).delete("/api/statuses/DONE");
    expect(res.status).toBe(204);
  });

  it("S-6: DELETE the last remaining status is 409", async () => {
    await request(app).delete("/api/statuses/DONE");
    await request(app).delete("/api/statuses/IN_PROGRESS");
    const res = await request(app).delete("/api/statuses/TODO");
    expect(res.status).toBe(409);
    expect(res.body.error).toContain("最後");
  });
});
