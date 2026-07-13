import { Router } from "express";
import { prisma } from "../db.js";
import { PRIORITIES } from "../constants.js";

const router = Router();

router.get("/", async (req, res) => {
  const { projectId } = req.query as { projectId?: string };
  const where = projectId ? { projectId } : { project: { archived: false } };

  const statuses = await prisma.status.findMany({ orderBy: { order: "asc" } });
  const doneIds = statuses.filter((s) => s.isDone).map((s) => s.id);

  const [total, byStatusRaw, byPriorityRaw, overdue, dueSoon, completedLast7Days] =
    await Promise.all([
      prisma.task.count({ where }),
      prisma.task.groupBy({ by: ["status"], where, _count: true }),
      prisma.task.groupBy({ by: ["priority"], where, _count: true }),
      prisma.task.count({
        where: { ...where, status: { notIn: doneIds }, dueDate: { lt: new Date() } },
      }),
      prisma.task.count({
        where: {
          ...where,
          status: { notIn: doneIds },
          dueDate: { gte: new Date(), lte: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000) },
        },
      }),
      prisma.task.count({
        where: {
          ...where,
          status: { in: doneIds },
          updatedAt: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) },
        },
      }),
    ]);

  const byStatus: Record<string, number> = {};
  for (const s of statuses) byStatus[s.id] = 0;
  for (const row of byStatusRaw) byStatus[row.status] = row._count;

  const byPriority = Object.fromEntries(PRIORITIES.map((p) => [p, 0])) as Record<string, number>;
  for (const row of byPriorityRaw) byPriority[row.priority] = row._count;

  const done = doneIds.reduce((sum, id) => sum + (byStatus[id] ?? 0), 0);
  const completionRate = total > 0 ? Math.round((done / total) * 1000) / 10 : 0;

  res.json({
    total,
    byStatus,
    byPriority,
    overdue,
    dueSoon,
    completedLast7Days,
    completionRate,
  });
});

export default router;
