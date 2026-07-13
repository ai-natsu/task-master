import { useMemo } from "react";
import {
  DndContext,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { SortableContext, arrayMove, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Task } from "../types";
import { buildTaskTree, type TaskTreeNode } from "../utils/tree";
import { TaskNode } from "./TaskNode";
import { useReorderTasks } from "../api/tasks";

interface Props {
  tasks: Task[];
  onStatusChange: (id: string, status: string) => void;
  onEdit: (node: TaskTreeNode) => void;
  onDelete: (node: TaskTreeNode) => void;
  onAddSubtask: (parentId: string) => void;
}

export function TaskTree({ tasks, onStatusChange, onEdit, onDelete, onAddSubtask }: Props) {
  const tree = useMemo(() => buildTaskTree(tasks), [tasks]);
  const taskById = useMemo(() => new Map(tasks.map((t) => [t.id, t])), [tasks]);
  const reorder = useReorderTasks();

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const activeTask = taskById.get(String(active.id));
    const overTask = taskById.get(String(over.id));
    if (!activeTask || !overTask) return;
    if (activeTask.parentId !== overTask.parentId) return;

    const siblings = tasks
      .filter((t) => t.parentId === activeTask.parentId)
      .sort((a, b) => a.order - b.order);
    const oldIndex = siblings.findIndex((t) => t.id === activeTask.id);
    const newIndex = siblings.findIndex((t) => t.id === overTask.id);
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(siblings, oldIndex, newIndex);
    reorder.mutate(reordered.map((t, i) => ({ id: t.id, order: i })));
  }

  if (tree.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400 dark:border-slate-700">
        タスクがありません。「新しいタスク」から追加してください。
      </div>
    );
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={tree.map((n) => n.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-0.5">
          {tree.map((node) => (
            <TaskNode
              key={node.id}
              node={node}
              depth={0}
              onStatusChange={onStatusChange}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddSubtask={onAddSubtask}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}
