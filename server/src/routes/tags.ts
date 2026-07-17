import { Router } from "express";
import { prisma } from "../db.js";
import { tagCreateSchema as createSchema } from "../schemas.js";

const router = Router();

router.get("/", async (_req, res) => {
  const tags = await prisma.tag.findMany({ orderBy: { name: "asc" } });
  res.json(tags);
});

router.post("/", async (req, res) => {
  const parsed = createSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  try {
    const tag = await prisma.tag.create({ data: parsed.data });
    res.status(201).json(tag);
  } catch {
    res.status(409).json({ error: "Tag already exists" });
  }
});

router.delete("/:id", async (req, res) => {
  try {
    await prisma.tag.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    res.status(404).json({ error: "Tag not found" });
  }
});

export default router;
