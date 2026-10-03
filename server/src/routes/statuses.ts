import { Router } from "express";
import { prisma } from "../db.js";
import {
  statusCreateSchema as createSchema,
  statusUpdateSchema as updateSchema,
  statusReorderSchema as reorderSchema,
} from "../schemas.js";
import { MSG, sendError, sendValidationError } from "../errors.js";

const router = Router();

router.get("/", async (_req, res) => {
  const statuses = await prisma.status.findMany({ orderBy: { order: "asc" } });
  res.json(statuses);
});

router.post("/", async (req, res) => {
  const parsed = createSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  const maxOrder = await prisma.status.aggregate({ _max: { order: true } });
  const status = await prisma.status.create({
    data: { ...parsed.data, order: (maxOrder._max.order ?? -1) + 1 },
  });
  res.status(201).json(status);
});

router.patch("/reorder", async (req, res) => {
  const parsed = reorderSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  await prisma.$transaction(
    parsed.data.ids.map((id, index) =>
      prisma.status.update({ where: { id }, data: { order: index } })
    )
  );
  res.json({ ok: true });
});

router.patch("/:id", async (req, res) => {
  const parsed = updateSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  try {
    const status = await prisma.status.update({
      where: { id: req.params.id },
      data: parsed.data,
    });
    res.json(status);
  } catch {
    sendError(res, 404, MSG.statusNotFound);
  }
});

router.delete("/:id", async (req, res) => {
  const inUse = await prisma.task.count({ where: { status: req.params.id } });
  if (inUse > 0) {
    return sendError(res, 409, MSG.statusInUse, { count: inUse });
  }
  const total = await prisma.status.count();
  if (total <= 1) {
    return sendError(res, 409, MSG.lastStatus);
  }
  try {
    await prisma.status.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    sendError(res, 404, MSG.statusNotFound);
  }
});

export default router;
