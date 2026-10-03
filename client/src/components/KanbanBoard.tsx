import {
  DndContext,
  DragOverlay,
  PointerSensor,
  pointerWithin,
  rectIntersection,
  useDroppable,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useMemo, useState } from "react";
import clsx from "clsx";
import { format } from "date-fns";
import { isOverdue } from "../utils/due";
import type { StatusDef, Task } from "../types";
import { PriorityBadge, TagPill } from "./Badges";
import { useReorderTasks, useUpdateTask } from "../api/tasks";
import { useStatuses } from "../api/statuses";
import { planKanbanDrag } from "../utils/dnd";

interface Props {
  tasks: Task[];
  onEdit: (task: Task) => void;
}

function KanbanCard({ task, isDone, onEdit, dragging }: { task: Task; isDone: boolean; onEdit?: (task: Task) => void; dragging?: boolean }) {
  const overdue = task.dueDate && !isDone && isOverdue(task.dueDate);
  return (
    <div
      onDoubleClick={() => onEdit?.(task)}
      className={clsx(
        "cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-sm hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-600",
        dragging && "rotate-2 shadow-lg ring-2 ring-indigo-400"
      )}
    >
      <div className={clsx("text-sm font-medium", isDone && "text-slate-400 line-through")}>
        {task.title}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <PriorityBadge priority={task.priority} />
        {task.tags.map((t) => (
          <TagPill key={t.id} tag={t} />
        ))}
        {task.dueDate && (
          <span className={clsx("text-xs", overdue ? "font-semibold text-red-600" : "text-slate-400")}>
            {format(new Date(task.dueDate), "MM/dd")}
          </span>
        )}
      </div>
    </div>
  );
}

function SortableCard({ task, isDone, onEdit }: { task: Task; isDone: boolean; onEdit: (task: Task) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
    data: { type: "card", statusId: task.status },
  });
  const style = { transform: CSS.Transform.toString(transform), transition };
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className={isDragging ? "opacity-30" : undefined}>
      <KanbanCard task={task} isDone={isDone} onEdit={onEdit} />
    </div>
  );
}

function Column({ status, tasks, onEdit }: { status: StatusDef; tasks: Task[]; onEdit: (task: Task) => void }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `column:${status.id}`,
    data: { type: "column", statusId: status.id },
  });
  return (
    <div
      ref={setNodeRef}
      data-testid={`kanban-col-${status.id}`}
      className={clsx(
        "flex min-h-[300px] w-64 shrink-0 flex-col gap-2 rounded-xl border border-slate-200 bg-slate-100/60 p-3 dark:border-slate-800 dark:bg-slate-900/60",
        isOver && "border-indigo-400 bg-indigo-50/60 dark:bg-indigo-950/40"
      )}
    >
      <div className="mb-1 flex items-center justify-between px-1">
        <span className="flex items-center gap-1.5 text-sm font-semibold">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: status.color }} />
          {status.label}
        </span>
        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-300">
          {tasks.length}
        </span>
      </div>
      <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
        {tasks.map((task) => (
          <SortableCard key={task.id} task={task} isDone={status.isDone} onEdit={onEdit} />
        ))}
      </SortableContext>
      {tasks.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 p-4 text-center text-xs text-slate-400 dark:border-slate-700">
          ここにドロップ
        </div>
      )}
    </div>
  );
}

const collisionDetection: CollisionDetection = (args) => {
  const pointerCollisions = pointerWithin(args);
  return pointerCollisions.length > 0 ? pointerCollisions : rectIntersection(args);
};

export function KanbanBoard({ tasks, onEdit }: Props) {
  const { data: statuses = [] } = useStatuses();
  const updateTask = useUpdateTask();
  const reorder = useReorderTasks();
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const columns = useMemo(() => {
    const map: Record<string, Task[]> = {};
    for (const s of statuses) map[s.id] = [];
    for (const t of tasks) (map[t.status] ??= []).push(t);
    for (const id of Object.keys(map)) map[id].sort((a, b) => a.order - b.order);
    return map;
  }, [tasks, statuses]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveTask(tasks.find((t) => t.id === event.active.id) ?? null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const overData = over.data.current as { type?: string; statusId?: string } | undefined;
    if (overData?.type !== "card" && overData?.type !== "column") return;

    const plan = planKanbanDrag(tasks, String(active.id), {
      id: String(over.id),
      type: overData.type,
      statusId: overData.statusId,
    });

    if (plan.statusChange) updateTask.mutate(plan.statusChange);
    if (plan.reorder) reorder.mutate(plan.reorder);
  };

  const activeStatusDef = activeTask ? statuses.find((s) => s.id === activeTask.status) : undefined;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={collisionDetection}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-2">
        {statuses.map((status) => (
          <Column key={status.id} status={status} tasks={columns[status.id] ?? []} onEdit={onEdit} />
        ))}
      </div>
      <DragOverlay>
        {activeTask && <KanbanCard task={activeTask} isDone={activeStatusDef?.isDone ?? false} dragging />}
      </DragOverlay>
    </DndContext>
  );
}
