import { arrayMove } from "@dnd-kit/sortable";
import type { Task } from "../types";

export type ReorderItem = { id: string; order: number };

/**
 * Pure decision logic for a kanban drag. Given the current task list and the
 * active/over identifiers, returns the intended side effects:
 *   - `statusChange`: set when the card moved to a different column
 *   - `reorder`: the new {id, order} list to persist (undefined = no-op)
 * The component wires these to `updateTask` / `reorder` mutations.
 */
export function planKanbanDrag(
  tasks: Task[],
  activeId: string,
  over: { id: string; type: "card" | "column"; statusId?: string } | null
): { statusChange?: { id: string; status: string }; reorder?: ReorderItem[] } {
  if (!over) return {};

  const task = tasks.find((t) => t.id === activeId);
  if (!task) return {};

  const columns: Record<string, Task[]> = {};
  for (const t of tasks) (columns[t.status] ??= []).push(t);
  for (const id of Object.keys(columns)) columns[id].sort((a, b) => a.order - b.order);

  let targetStatus: string;
  let targetIndex: number;

  if (over.type === "card") {
    const overTask = tasks.find((t) => t.id === over.id);
    if (!overTask) return {};
    targetStatus = overTask.status;
    targetIndex = (columns[targetStatus] ?? []).findIndex((t) => t.id === overTask.id);
    if (targetIndex < 0) targetIndex = 0;
  } else {
    targetStatus = over.statusId!;
    targetIndex = (columns[targetStatus] ?? []).length;
  }

  const source = columns[task.status] ?? [];

  if (targetStatus === task.status) {
    const oldIndex = source.findIndex((t) => t.id === task.id);
    if (oldIndex === -1 || oldIndex === targetIndex) return {};
    const newList = arrayMove(source, oldIndex, targetIndex);
    return { reorder: newList.map((t, i) => ({ id: t.id, order: i })) };
  }

  const target = [...(columns[targetStatus] ?? [])];
  target.splice(targetIndex, 0, task);
  return {
    statusChange: { id: task.id, status: targetStatus },
    reorder: [
      ...target.map((t, i) => ({ id: t.id, order: i })),
      ...source.filter((t) => t.id !== task.id).map((t, i) => ({ id: t.id, order: i })),
    ],
  };
}

export type RowDropZone = "before" | "after" | "child";
export type RowDropItem = ReorderItem & { parentId?: string | null };

function isDescendantOrSelf(tasks: Task[], ancestorId: string, taskId: string): boolean {
  const parentOf = new Map(tasks.map((t) => [t.id, t.parentId]));
  const seen = new Set<string>();
  let current: string | null | undefined = taskId;
  while (current && !seen.has(current)) {
    if (current === ancestorId) return true;
    seen.add(current);
    current = parentOf.get(current);
  }
  return false;
}

/**
 * Pure decision logic for dropping a Gantt row (reorder + reparent).
 * zone: "before" / "after" insert as a sibling just before / after the target;
 * "child" appends it as the target's last child. A task can't be moved under
 * itself or its own descendants. Returns `{}` when nothing changes. Only the
 * moved task's item carries `parentId`, and only when its parent changes.
 */
export function planRowDrop(
  tasks: Task[],
  activeId: string,
  targetId: string,
  zone: RowDropZone
): { reorder?: RowDropItem[] } {
  if (activeId === targetId) return {};
  const active = tasks.find((t) => t.id === activeId);
  const target = tasks.find((t) => t.id === targetId);
  if (!active || !target) return {};
  if (isDescendantOrSelf(tasks, activeId, targetId)) return {};

  const newParent = zone === "child" ? target.id : target.parentId;
  const byOrder = (a: Task, b: Task) => a.order - b.order;
  const siblings = tasks.filter((t) => t.parentId === newParent && t.id !== activeId).sort(byOrder);
  let index: number;
  if (zone === "child") {
    index = siblings.length;
  } else {
    const targetIndex = siblings.findIndex((t) => t.id === targetId);
    index = zone === "before" ? targetIndex : targetIndex + 1;
  }
  siblings.splice(index, 0, active);

  const parentChanged = active.parentId !== newParent;
  const reorder: RowDropItem[] = siblings.map((t, i) =>
    t.id === activeId && parentChanged ? { id: t.id, order: i, parentId: newParent } : { id: t.id, order: i }
  );

  if (parentChanged) {
    // 元の親の兄弟も詰め直す（順序の欠番を残さない）
    const oldSiblings = tasks.filter((t) => t.parentId === active.parentId && t.id !== activeId).sort(byOrder);
    reorder.push(...oldSiblings.map((t, i) => ({ id: t.id, order: i })));
  } else {
    const before = tasks.filter((t) => t.parentId === active.parentId).sort(byOrder);
    if (before.every((t, i) => t.id === siblings[i]?.id)) return {};
  }
  return { reorder };
}
