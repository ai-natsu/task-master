import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import request from "supertest";
import { afterAll, describe, expect, it } from "vitest";
import { createApp } from "../../src/app.js";

// 本番：ビルド済みの画面（client/dist）を、API と同じサーバーから配信する。
const dir = mkdtempSync(join(tmpdir(), "taskmaster-dist-"));
mkdirSync(join(dir, "assets"));
writeFileSync(join(dir, "index.html"), "<!doctype html><title>TaskMaster</title><div id=root></div>");
writeFileSync(join(dir, "assets", "app.js"), "console.log('ok');");

afterAll(() => rmSync(dir, { recursive: true, force: true }));

describe("画面の配信（staticDir を指定した場合）", () => {
  const app = createApp({ staticDir: dir });

  it("S-1: / で index.html を返す", async () => {
    const res = await request(app).get("/");
    expect(res.status).toBe(200);
    expect(res.text).toContain("TaskMaster");
  });

  it("S-2: 画面のパス（/projects/xxx、/settings）でも index.html を返す（再読み込み・URL の直接入力のため）", async () => {
    for (const path of ["/projects/abc", "/settings"]) {
      const res = await request(app).get(path);
      expect(res.status, path).toBe(200);
      expect(res.text).toContain("TaskMaster");
    }
  });

  it("S-3: 静的ファイル（assets/）をそのまま返す", async () => {
    const res = await request(app).get("/assets/app.js");
    expect(res.status).toBe(200);
    expect(res.text).toContain("console.log");
  });

  it("S-4: /api 配下は、画面ではなく API が応答する（存在しない API は 404）", async () => {
    expect((await request(app).get("/api/health")).body).toEqual({ ok: true });
    expect((await request(app).get("/api/no-such-api")).status).toBe(404);
  });
});

describe("画面の配信（staticDir を指定しない場合）", () => {
  it("S-5: 従来どおり、画面のパスは 404", async () => {
    const res = await request(createApp()).get("/projects/abc");
    expect(res.status).toBe(404);
  });
});
