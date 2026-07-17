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

/**
 * Pure decision logic for a tree drag. Reordering only happens within the same
 * parent group; a cross-parent drag is a no-op (moving between parents is done
 * via the edit form, not by dragging).
 */
export function planTreeDrag(
  tasks: Task[],
  activeId: string,
  overId: string | null
): { reorder?: ReorderItem[] } {
  if (!overId || activeId === overId) return {};
  const active = tasks.find((t) => t.id === activeId);
  const over = tasks.find((t) => t.id === overId);
  if (!active || !over) return {};
  if (active.parentId !== over.parentId) return {};

  const siblings = tasks
    .filter((t) => t.parentId === active.parentId)
    .sort((a, b) => a.order - b.order);
  const oldIndex = siblings.findIndex((t) => t.id === active.id);
  const newIndex = siblings.findIndex((t) => t.id === over.id);
  if (oldIndex === -1 || newIndex === -1) return {};

  const reordered = arrayMove(siblings, oldIndex, newIndex);
  return { reorder: reordered.map((t, i) => ({ id: t.id, order: i })) };
}
