import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import request from "supertest";
import "../helpers/setup.js";
import { createApp } from "../../src/app.js";
import { prisma } from "../../src/db.js";
import { makeProject, makeTask, seedStatuses } from "../helpers/factories.js";

const app = createApp();

const NOW = new Date("2026-07-14T12:00:00.000Z");

beforeEach(async () => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW);
  await seedStatuses();
});

afterEach(() => {
  vi.useRealTimers();
});

// 期限日は UTC 0 時の日付として保存される（フォームの YYYY-MM-DD → ISO）。今日を基準に n 日後の日付。
function dueOn(n: number) {
  return new Date(Date.UTC(2026, 6, 14 + n));
}

describe("/api/stats", () => {
  it("ST-1..ST-4: total, byStatus, byPriority, completionRate", async () => {
    const p = await makeProject();
    await makeTask(p.id, { status: "TODO", priority: "LOW" });
    await makeTask(p.id, { status: "IN_PROGRESS", priority: "HIGH" });
    await makeTask(p.id, { status: "DONE", priority: "HIGH" });
    await makeTask(p.id, { status: "DONE", priority: "URGENT" });

    const res = await request(app).get("/api/stats");
    expect(res.body.total).toBe(4);
    expect(res.body.byStatus).toMatchObject({ TODO: 1, IN_PROGRESS: 1, DONE: 2 });
    expect(res.body.byPriority).toMatchObject({ LOW: 1, MEDIUM: 0, HIGH: 2, URGENT: 1 });
    // 2 done of 4 = 50%
    expect(res.body.completionRate).toBe(50);
  });

  it("ST-5: multiple isDone statuses both count as completed", async () => {
    await prisma.status.create({
      data: { id: "WITHDRAWN", label: "取下げ", color: "#94a3b8", order: 3, isDone: true },
    });
    const p = await makeProject();
    await makeTask(p.id, { status: "TODO" });
    await makeTask(p.id, { status: "DONE" });
    await makeTask(p.id, { status: "WITHDRAWN" });

    const res = await request(app).get("/api/stats");
    // 2 of 3 are done (DONE + WITHDRAWN) => 66.7
    expect(res.body.completionRate).toBe(66.7);
  });

  it("ST-6: overdue counts non-done past-due only", async () => {
    const p = await makeProject();
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(-1) }); // overdue
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(0) }); // due today is not overdue
    await makeTask(p.id, { status: "DONE", dueDate: dueOn(-1) }); // done, not overdue
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(5) }); // future

    const res = await request(app).get("/api/stats");
    expect(res.body.overdue).toBe(1);
  });

  it("ST-7: dueSoon counts non-done due from today through 3 days later (4 days)", async () => {
    const p = await makeProject();
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(0) }); // today: soon
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(3) }); // +3 days: soon (last day)
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(4) }); // +4 days: later
    await makeTask(p.id, { status: "TODO", dueDate: dueOn(-1) }); // overdue, not soon
    await makeTask(p.id, { status: "DONE", dueDate: dueOn(1) }); // done

    const res = await request(app).get("/api/stats");
    expect(res.body.dueSoon).toBe(2);
  });

  it("ST-8: global stats exclude archived projects", async () => {
    const live = await makeProject();
    await makeTask(live.id);
    const arch = await makeProject({ archived: true });
    await makeTask(arch.id);
    await makeTask(arch.id);

    const res = await request(app).get("/api/stats");
    expect(res.body.total).toBe(1);
  });

  it("ST-9: total=0 yields completionRate 0 (no divide by zero)", async () => {
    const res = await request(app).get("/api/stats");
    expect(res.body.total).toBe(0);
    expect(res.body.completionRate).toBe(0);
  });
});
