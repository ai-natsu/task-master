import { useMemo } from "react";
import {
  DndContext,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Task } from "../types";
import { buildTaskTree, type TaskTreeNode } from "../utils/tree";
import { TaskNode } from "./TaskNode";
import { useReorderTasks } from "../api/tasks";
import { planTreeDrag } from "../utils/dnd";

interface Props {
  tasks: Task[];
  onStatusChange: (id: string, status: string) => void;
  onEdit: (node: TaskTreeNode) => void;
  onDelete: (node: TaskTreeNode) => void;
  onAddSubtask: (parentId: string) => void;
}

export function TaskTree({ tasks, onStatusChange, onEdit, onDelete, onAddSubtask }: Props) {
  const tree = useMemo(() => buildTaskTree(tasks), [tasks]);
  const reorder = useReorderTasks();

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    const plan = planTreeDrag(tasks, String(active.id), over ? String(over.id) : null);
    if (plan.reorder) reorder.mutate(plan.reorder);
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
