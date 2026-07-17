import { Router } from "express";
import { prisma } from "../db.js";
import {
  statusCreateSchema as createSchema,
  statusUpdateSchema as updateSchema,
  statusReorderSchema as reorderSchema,
} from "../schemas.js";

const router = Router();

router.get("/", async (_req, res) => {
  const statuses = await prisma.status.findMany({ orderBy: { order: "asc" } });
  res.json(statuses);
});

router.post("/", async (req, res) => {
  const parsed = createSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  const maxOrder = await prisma.status.aggregate({ _max: { order: true } });
  const status = await prisma.status.create({
    data: { ...parsed.data, order: (maxOrder._max.order ?? -1) + 1 },
  });
  res.status(201).json(status);
});

router.patch("/reorder", async (req, res) => {
  const parsed = reorderSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  await prisma.$transaction(
    parsed.data.ids.map((id, index) =>
      prisma.status.update({ where: { id }, data: { order: index } })
    )
  );
  res.json({ ok: true });
});

router.patch("/:id", async (req, res) => {
  const parsed = updateSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  try {
    const status = await prisma.status.update({
      where: { id: req.params.id },
      data: parsed.data,
    });
    res.json(status);
  } catch {
    res.status(404).json({ error: "Status not found" });
  }
});

router.delete("/:id", async (req, res) => {
  const inUse = await prisma.task.count({ where: { status: req.params.id } });
  if (inUse > 0) {
    return res
      .status(409)
      .json({ error: `このステータスは ${inUse} 件のタスクで使用中のため削除できません` });
  }
  const total = await prisma.status.count();
  if (total <= 1) {
    return res.status(409).json({ error: "最後のステータスは削除できません" });
  }
  try {
    await prisma.status.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    res.status(404).json({ error: "Status not found" });
  }
});

export default router;
