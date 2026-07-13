import { Router } from "express";
import { z } from "zod";
import { prisma } from "../db.js";
import { PRIORITIES } from "../constants.js";

const router = Router();

const createSchema = z.object({
  title: z.string().min(1).max(300),
  description: z.string().max(5000).optional(),
  projectId: z.string(),
  parentId: z.string().nullable().optional(),
  status: z.string().optional(),
  priority: z.enum(PRIORITIES).optional(),
  startDate: z.string().datetime().nullable().optional(),
  dueDate: z.string().datetime().nullable().optional(),
  tagIds: z.array(z.string()).optional(),
});

const updateSchema = z.object({
  title: z.string().min(1).max(300).optional(),
  description: z.string().max(5000).nullable().optional(),
  status: z.string().optional(),
  priority: z.enum(PRIORITIES).optional(),
  startDate: z.string().datetime().nullable().optional(),
  dueDate: z.string().datetime().nullable().optional(),
  tagIds: z.array(z.string()).optional(),
});

const moveSchema = z.object({
  parentId: z.string().nullable().optional(),
  projectId: z.string().optional(),
  order: z.number().int().optional(),
});

const reorderSchema = z.object({
  items: z.array(
    z.object({
      id: z.string(),
      order: z.number().int(),
      parentId: z.string().nullable().optional(),
      projectId: z.string().optional(),
    })
  ),
});

const taskInclude = {
  tags: { include: { tag: true } },
} as const;

function serialize(task: any) {
  return {
    ...task,
    tags: task.tags?.map((t: any) => t.tag) ?? [],
  };
}

// Detect whether `candidateAncestorId` is `taskId` itself or one of its descendants,
// to reject moves that would create a cycle in the subtask tree.
async function isDescendantOrSelf(taskId: string, candidateAncestorId: string): Promise<boolean> {
  if (taskId === candidateAncestorId) return true;
  const children = await prisma.task.findMany({
    where: { parentId: taskId },
    select: { id: true },
  });
  for (const child of children) {
    if (await isDescendantOrSelf(child.id, candidateAncestorId)) return true;
  }
  return false;
}

router.get("/", async (req, res) => {
  const { projectId, status, priority, tagId, search, parentId } = req.query as Record<
    string,
    string | undefined
  >;

  const where: any = {};
  if (projectId) where.projectId = projectId;
  else where.project = { archived: false };
  if (status) where.status = status;
  if (priority) where.priority = priority;
  if (parentId === "null") where.parentId = null;
  else if (parentId) where.parentId = parentId;
  if (search) {
    where.OR = [
      { title: { contains: search } },
      { description: { contains: search } },
    ];
  }
  if (tagId) where.tags = { some: { tagId } };

  const tasks = await prisma.task.findMany({
    where,
    include: taskInclude,
    orderBy: [{ order: "asc" }, { createdAt: "asc" }],
  });
  res.json(tasks.map(serialize));
});

router.post("/", async (req, res) => {
  const parsed = createSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const { tagIds, dueDate, ...rest } = parsed.data;

  if (rest.parentId) {
    const parent = await prisma.task.findUnique({ where: { id: rest.parentId } });
    if (!parent) return res.status(400).json({ error: "Parent task not found" });
  }

  if (rest.status) {
    const exists = await prisma.status.findUnique({ where: { id: rest.status } });
    if (!exists) return res.status(400).json({ error: "Invalid status" });
  } else {
    const first = await prisma.status.findFirst({ orderBy: { order: "asc" } });
    if (!first) return res.status(400).json({ error: "No statuses defined" });
    rest.status = first.id;
  }

  const maxOrder = await prisma.task.aggregate({
    _max: { order: true },
    where: { projectId: rest.projectId, parentId: rest.parentId ?? null },
  });

  const task = await prisma.task.create({
    data: {
      ...rest,
      dueDate: dueDate ?? null,
      order: (maxOrder._max.order ?? -1) + 1,
      tags: tagIds ? { create: tagIds.map((tagId) => ({ tagId })) } : undefined,
    },
    include: taskInclude,
  });
  res.status(201).json(serialize(task));
});

router.patch("/reorder", async (req, res) => {
  const parsed = reorderSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  await prisma.$transaction(
    parsed.data.items.map(({ id, order, parentId, projectId }) =>
      prisma.task.update({
        where: { id },
        data: {
          order,
          ...(parentId !== undefined ? { parentId } : {}),
          ...(projectId !== undefined ? { projectId } : {}),
        },
      })
    )
  );
  res.json({ ok: true });
});

router.get("/:id", async (req, res) => {
  const task = await prisma.task.findUnique({
    where: { id: req.params.id },
    include: taskInclude,
  });
  if (!task) return res.status(404).json({ error: "Task not found" });
  res.json(serialize(task));
});

router.patch("/:id", async (req, res) => {
  const parsed = updateSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const { tagIds, ...rest } = parsed.data;

  if (rest.status) {
    const exists = await prisma.status.findUnique({ where: { id: rest.status } });
    if (!exists) return res.status(400).json({ error: "Invalid status" });
  }

  try {
    const task = await prisma.task.update({
      where: { id: req.params.id },
      data: {
        ...rest,
        tags: tagIds
          ? {
              deleteMany: {},
              create: tagIds.map((tagId) => ({ tagId })),
            }
          : undefined,
      },
      include: taskInclude,
    });
    res.json(serialize(task));
  } catch {
    res.status(404).json({ error: "Task not found" });
  }
});

router.patch("/:id/move", async (req, res) => {
  const parsed = moveSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });

  const { id } = req.params;
  const { parentId } = parsed.data;

  if (parentId) {
    if (await isDescendantOrSelf(id, parentId)) {
      return res.status(400).json({ error: "Cannot move a task under itself or its own subtask" });
    }
  }

  try {
    const task = await prisma.task.update({
      where: { id },
      data: parsed.data,
      include: taskInclude,
    });
    res.json(serialize(task));
  } catch {
    res.status(404).json({ error: "Task not found" });
  }
});

router.delete("/:id", async (req, res) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id } });
    res.status(204).end();
  } catch {
    res.status(404).json({ error: "Task not found" });
  }
});

export default router;
