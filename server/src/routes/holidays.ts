import { Router } from "express";
import { prisma } from "../db.js";
import {
  holidayBulkSchema as bulkSchema,
  holidayUpdateSchema as updateSchema,
  holidayUpsertSchema as upsertSchema,
} from "../schemas.js";
import { MSG, sendError, sendValidationError } from "../errors.js";

const router = Router();

router.get("/", async (_req, res) => {
  const holidays = await prisma.holiday.findMany({ orderBy: { date: "asc" } });
  res.json(holidays);
});

// 日付が一致する行があれば名称を上書き、無ければ作成する
router.post("/", async (req, res) => {
  const parsed = upsertSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  const { date, name } = parsed.data;
  const holiday = await prisma.holiday.upsert({
    where: { date },
    update: { name },
    create: { date, name },
  });
  res.status(201).json(holiday);
});

// CSV 取り込み用の一括登録（1 トランザクション）
router.post("/bulk", async (req, res) => {
  const parsed = bulkSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  await prisma.$transaction(
    parsed.data.rows.map(({ date, name }) =>
      prisma.holiday.upsert({ where: { date }, update: { name }, create: { date, name } })
    )
  );
  res.json({ count: parsed.data.rows.length });
});

router.patch("/:id", async (req, res) => {
  const parsed = updateSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  try {
    const holiday = await prisma.holiday.update({ where: { id: req.params.id }, data: parsed.data });
    res.json(holiday);
  } catch {
    sendError(res, 404, MSG.holidayNotFound);
  }
});

router.delete("/:id", async (req, res) => {
  try {
    await prisma.holiday.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    sendError(res, 404, MSG.holidayNotFound);
  }
});

export default router;
