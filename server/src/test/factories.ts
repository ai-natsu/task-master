import { prisma } from "../db.js";

export const DEFAULT_STATUSES = [
  { id: "TODO", label: "未着手", color: "#64748b", order: 0, isDone: false },
  { id: "IN_PROGRESS", label: "進行中", color: "#6366f1", order: 1, isDone: false },
  { id: "DONE", label: "完了", color: "#10b981", order: 2, isDone: true },
];

export async function seedStatuses() {
  for (const s of DEFAULT_STATUSES) {
    await prisma.status.create({ data: s });
  }
}

let projectSeq = 0;
export async function makeProject(overrides: Partial<{ name: string; archived: boolean; order: number }> = {}) {
  return prisma.project.create({
    data: {
      name: overrides.name ?? `Project ${++projectSeq}`,
      archived: overrides.archived ?? false,
      order: overrides.order ?? 0,
    },
  });
}

export async function makeTask(
  projectId: string,
  overrides: Partial<{
    title: string;
    status: string;
    priority: string;
    parentId: string | null;
    order: number;
    dueDate: Date | null;
    startDate: Date | null;
  }> = {}
) {
  return prisma.task.create({
    data: {
      title: overrides.title ?? "Task",
      status: overrides.status ?? "TODO",
      priority: overrides.priority ?? "MEDIUM",
      parentId: overrides.parentId ?? null,
      order: overrides.order ?? 0,
      dueDate: overrides.dueDate ?? null,
      startDate: overrides.startDate ?? null,
      projectId,
    },
  });
}
