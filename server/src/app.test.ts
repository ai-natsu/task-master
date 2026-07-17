import { describe, it, expect } from "vitest";
import request from "supertest";
import "./test/setup.js";
import { createApp } from "./app.js";

const app = createApp();

// These cover the parts of app.ts that the route tests never exercise:
// CORS and /api/health sit outside their request path, so deleting either
// would leave every other suite green.
describe("app wiring", () => {
  it("A-1: GET /api/health responds", async () => {
    const res = await request(app).get("/api/health");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ ok: true });
  });

  it("A-2: unknown path returns 404", async () => {
    const res = await request(app).get("/api/does-not-exist");
    expect(res.status).toBe(404);
  });

  it("A-3: CORS header is present (browser access depends on it)", async () => {
    const res = await request(app).get("/api/health");
    expect(res.headers["access-control-allow-origin"]).toBe("*");
  });

  it("A-4: JSON body parsing is enabled", async () => {
    // Reaching zod's 400 (rather than a crash) proves the body was parsed.
    const res = await request(app)
      .post("/api/projects")
      .set("Content-Type", "application/json")
      .send({ name: "" });
    expect(res.status).toBe(400);
  });

  it("A-5: all resource routers are mounted under /api", async () => {
    for (const path of ["/api/projects", "/api/tasks", "/api/tags", "/api/statuses", "/api/stats"]) {
      const res = await request(app).get(path);
      expect(res.status, `${path} should be routed`).not.toBe(404);
    }
  });
});
