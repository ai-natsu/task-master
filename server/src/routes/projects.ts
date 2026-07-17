import { Router } from "express";
import { prisma } from "../db.js";
import {
  projectCreateSchema as createSchema,
  projectUpdateSchema as updateSchema,
  projectReorderSchema as reorderSchema,
} from "../schemas.js";

const router = Router();

router.get("/", async (req, res) => {
  const includeArchived = req.query.includeArchived === "true";
  const projects = await prisma.project.findMany({
    where: includeArchived ? {} : { archived: false },
    orderBy: { order: "asc" },
    include: {
      _count: {
        select: { tasks: true },
      },
    },
  });
  res.json(projects);
});

router.post("/", async (req, res) => {
  const parsed = createSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  const maxOrder = await prisma.project.aggregate({ _max: { order: true } });
  const project = await prisma.project.create({
    data: {
      ...parsed.data,
      order: (maxOrder._max.order ?? -1) + 1,
    },
  });
  res.status(201).json(project);
});

router.patch("/reorder", async (req, res) => {
  const parsed = reorderSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  await prisma.$transaction(
    parsed.data.ids.map((id, index) =>
      prisma.project.update({ where: { id }, data: { order: index } })
    )
  );
  res.json({ ok: true });
});

router.get("/:id", async (req, res) => {
  const project = await prisma.project.findUnique({ where: { id: req.params.id } });
  if (!project) return res.status(404).json({ error: "Project not found" });
  res.json(project);
});

router.patch("/:id", async (req, res) => {
  const parsed = updateSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  try {
    const project = await prisma.project.update({
      where: { id: req.params.id },
      data: parsed.data,
    });
    res.json(project);
  } catch {
    res.status(404).json({ error: "Project not found" });
  }
});

router.delete("/:id", async (req, res) => {
  try {
    await prisma.project.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    res.status(404).json({ error: "Project not found" });
  }
});

export default router;
