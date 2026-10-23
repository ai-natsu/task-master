import { Router } from "express";
import { prisma } from "../db.js";
import { tagCreateSchema as createSchema, tagUpdateSchema as updateSchema } from "../schemas.js";
import { MSG, sendError, sendValidationError } from "../errors.js";

const router = Router();

router.get("/", async (_req, res) => {
  // _count.tasks = このタグが付いているタスクの件数（削除確認の表示に使う）
  const tags = await prisma.tag.findMany({
    orderBy: { name: "asc" },
    include: { _count: { select: { tasks: true } } },
  });
  res.json(tags);
});

router.post("/", async (req, res) => {
  const parsed = createSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  try {
    const tag = await prisma.tag.create({ data: parsed.data });
    res.status(201).json(tag);
  } catch {
    sendError(res, 409, MSG.tagExists);
  }
});

// 改名・色変更。名前が既存と重複する場合は 409
router.patch("/:id", async (req, res) => {
  const parsed = updateSchema.safeParse(req.body);
  if (!parsed.success) return sendValidationError(res, parsed.error);

  try {
    const tag = await prisma.tag.update({
      where: { id: req.params.id },
      data: parsed.data,
      include: { _count: { select: { tasks: true } } },
    });
    res.json(tag);
  } catch (e) {
    const code = (e as { code?: string }).code;
    if (code === "P2002") return sendError(res, 409, MSG.tagExists);
    sendError(res, 404, MSG.tagNotFound);
  }
});

router.delete("/:id", async (req, res) => {
  try {
    await prisma.tag.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    sendError(res, 404, MSG.tagNotFound);
  }
});

export default router;
