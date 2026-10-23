import { describe, it, expect, beforeEach } from "vitest";
import request from "supertest";
import "../helpers/setup.js";
import { createApp } from "../../src/app.js";
import { makeProject, makeTask, seedStatuses } from "../helpers/factories.js";

const app = createApp();

beforeEach(async () => {
  await seedStatuses();
});

// V1/V2 共通のエラーメッセージ（docs/BASIC_DESIGN.md §7.2）
describe("error messages", () => {
  it("E-1: not found errors use the common Japanese messages", async () => {
    const cases: [string, string][] = [
      ["/api/projects/nope", "プロジェクトが見つかりません"],
      ["/api/tasks/nope", "タスクが見つかりません"],
    ];
    for (const [path, message] of cases) {
      const res = await request(app).get(path);
      expect(res.status).toBe(404);
      expect(res.body).toEqual({ error: message });
    }
    expect((await request(app).delete("/api/tags/nope")).body.error).toBe("タグが見つかりません");
    expect((await request(app).delete("/api/holidays/nope")).body.error).toBe("祝日が見つかりません");
  });

  it("E-2: validation errors name the first offending field", async () => {
    const res = await request(app).post("/api/projects").send({ name: "" });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("入力内容を確認してください（name）");
    expect(res.body.key).toBe("入力内容を確認してください（{field}）");
    expect(res.body.params).toEqual({ field: "name" });
  });

  it("E-3: business rule errors (parent / status / cycle)", async () => {
    const project = await makeProject();
    const parent = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId: project.id, parentId: "nope" });
    expect(parent.body.error).toBe("親タスクが見つかりません");

    const status = await request(app)
      .post("/api/tasks")
      .send({ title: "t", projectId: project.id, status: "nope" });
    expect(status.body.error).toBe("指定のステータスが存在しません");

    const a = await makeTask(project.id, { title: "A" });
    const b = await makeTask(project.id, { title: "B", parentId: a.id });
    const cycle = await request(app).patch(`/api/tasks/${a.id}/move`).send({ parentId: b.id });
    expect(cycle.status).toBe(400);
    expect(cycle.body.error).toBe("タスクを自分自身またはその配下には移動できません");
  });

  it("E-4: parameterized messages also return the template and params for translation", async () => {
    const project = await makeProject();
    await makeTask(project.id, { status: "TODO" });
    const res = await request(app).delete("/api/statuses/TODO");
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("このステータスは 1 件のタスクで使用中のため削除できません");
    expect(res.body.key).toBe("このステータスは {count} 件のタスクで使用中のため削除できません");
    expect(res.body.params).toEqual({ count: 1 });
  });

  it("E-5: duplicate tag names are 409 with the common message (create and rename)", async () => {
    await request(app).post("/api/tags").send({ name: "a" });
    const b = await request(app).post("/api/tags").send({ name: "b" });
    const dup = await request(app).post("/api/tags").send({ name: "a" });
    expect(dup.status).toBe(409);
    expect(dup.body.error).toBe("タグが既に存在します");

    const rename = await request(app).patch(`/api/tags/${b.body.id}`).send({ name: "a" });
    expect(rename.status).toBe(409);
    expect(rename.body.error).toBe("タグが既に存在します");
  });

  it("E-6: broken JSON bodies and unknown ids never leak raw errors", async () => {
    const res = await request(app)
      .post("/api/projects")
      .set("Content-Type", "application/json")
      .send("{not json");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("入力内容を確認してください");
  });
});

describe("/api/tags management", () => {
  it("G-4: PATCH renames / recolors and GET returns the number of tagged tasks", async () => {
    const project = await makeProject();
    const task = await makeTask(project.id);
    const tag = await request(app).post("/api/tags").send({ name: "x" });
    await request(app).patch(`/api/tasks/${task.id}`).send({ tagIds: [tag.body.id] });

    const patched = await request(app)
      .patch(`/api/tags/${tag.body.id}`)
      .send({ name: "renamed", color: "#ff0000" });
    expect(patched.status).toBe(200);
    expect(patched.body).toMatchObject({ name: "renamed", color: "#ff0000" });

    const list = await request(app).get("/api/tags");
    expect(list.body[0]._count.tasks).toBe(1);
  });

  it("G-5: PATCH with nothing to update is 400, unknown id is 404", async () => {
    const tag = await request(app).post("/api/tags").send({ name: "x" });
    expect((await request(app).patch(`/api/tags/${tag.body.id}`).send({})).status).toBe(400);
    expect((await request(app).patch("/api/tags/nope").send({ name: "y" })).status).toBe(404);
  });
});
