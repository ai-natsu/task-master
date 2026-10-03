import { describe, it, expect } from "vitest";
import request from "supertest";
import "../test/setup.js";
import { createApp } from "../app.js";

const app = createApp();

describe("/api/holidays", () => {
  it("H-1: GET returns holidays in date ascending order", async () => {
    await request(app).post("/api/holidays").send({ date: "2026-05-05", name: "こどもの日" });
    await request(app).post("/api/holidays").send({ date: "2026-01-01", name: "元日" });

    const res = await request(app).get("/api/holidays");
    expect(res.status).toBe(200);
    expect(res.body.map((h: { date: string }) => h.date)).toEqual(["2026-01-01", "2026-05-05"]);
  });

  it("H-2: POST with an existing date overwrites the name (no duplicate dates)", async () => {
    await request(app).post("/api/holidays").send({ date: "2026-01-01", name: "元日" });
    const res = await request(app).post("/api/holidays").send({ date: "2026-01-01", name: "New Year" });
    expect(res.status).toBe(201);

    const list = await request(app).get("/api/holidays");
    expect(list.body).toHaveLength(1);
    expect(list.body[0].name).toBe("New Year");
  });

  it("H-3: POST rejects invalid dates and empty names with 400", async () => {
    for (const body of [
      { date: "2026-02-30", name: "x" },
      { date: "2026/01/01", name: "x" },
      { date: "2026-01-01", name: "   " },
      { name: "x" },
    ]) {
      const res = await request(app).post("/api/holidays").send(body);
      expect(res.status, JSON.stringify(body)).toBe(400);
    }
  });

  it("H-4: PATCH renames, 404 for unknown id", async () => {
    const created = await request(app).post("/api/holidays").send({ date: "2026-01-01", name: "元日" });
    const res = await request(app).patch(`/api/holidays/${created.body.id}`).send({ name: "元日（改）" });
    expect(res.status).toBe(200);
    expect(res.body.name).toBe("元日（改）");

    const missing = await request(app).patch("/api/holidays/nope").send({ name: "x" });
    expect(missing.status).toBe(404);
  });

  it("H-5: DELETE removes, 404 for unknown id", async () => {
    const created = await request(app).post("/api/holidays").send({ date: "2026-01-01", name: "元日" });
    expect((await request(app).delete(`/api/holidays/${created.body.id}`)).status).toBe(204);
    expect((await request(app).get("/api/holidays")).body).toHaveLength(0);
    expect((await request(app).delete("/api/holidays/nope")).status).toBe(404);
  });

  it("H-6: bulk registers new rows and overwrites rows with a matching date", async () => {
    await request(app).post("/api/holidays").send({ date: "2026-01-01", name: "old" });
    const res = await request(app)
      .post("/api/holidays/bulk")
      .send({
        rows: [
          { date: "2026-01-01", name: "元日" },
          { date: "2026-02-11", name: "建国記念の日" },
        ],
      });
    expect(res.status).toBe(200);
    expect(res.body.count).toBe(2);

    const list = await request(app).get("/api/holidays");
    expect(list.body.map((h: { name: string }) => h.name)).toEqual(["元日", "建国記念の日"]);
  });

  it("H-7: bulk is all-or-nothing when a row is invalid", async () => {
    const res = await request(app)
      .post("/api/holidays/bulk")
      .send({ rows: [{ date: "2026-01-01", name: "元日" }, { date: "bad", name: "x" }] });
    expect(res.status).toBe(400);
    expect((await request(app).get("/api/holidays")).body).toHaveLength(0);
  });
});
