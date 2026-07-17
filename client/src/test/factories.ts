import type { Task } from "../types";

let seq = 0;

export function makeTask(overrides: Partial<Task> = {}): Task {
  seq += 1;
  return {
    id: overrides.id ?? `t${seq}`,
    title: overrides.title ?? `Task ${seq}`,
    description: overrides.description ?? null,
    status: overrides.status ?? "TODO",
    priority: overrides.priority ?? "MEDIUM",
    startDate: overrides.startDate ?? null,
    dueDate: overrides.dueDate ?? null,
    order: overrides.order ?? 0,
    projectId: overrides.projectId ?? "p1",
    parentId: overrides.parentId ?? null,
    createdAt: overrides.createdAt ?? "2026-01-01T00:00:00.000Z",
    updatedAt: overrides.updatedAt ?? "2026-01-01T00:00:00.000Z",
    tags: overrides.tags ?? [],
  };
}
