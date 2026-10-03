import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import { format } from "date-fns";
import { isOverdue } from "../utils/due";
import type { TaskTreeNode } from "../utils/tree";
import { useStatuses } from "../api/statuses";
import { PriorityBadge, TagPill } from "./Badges";

interface Props {
  node: TaskTreeNode;
  depth: number;
  onStatusChange: (id: string, status: string) => void;
  onEdit: (node: TaskTreeNode) => void;
  onDelete: (node: TaskTreeNode) => void;
  onAddSubtask: (parentId: string) => void;
}

export function TaskNode({ node, depth, onStatusChange, onEdit, onDelete, onAddSubtask }: Props) {
  const [expanded, setExpanded] = useState(true);
  const { data: statuses = [] } = useStatuses();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: node.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const statusDef = statuses.find((s) => s.id === node.status);
  const isDone = statusDef?.isDone ?? false;
  const overdue = node.dueDate && !isDone && isOverdue(node.dueDate);

  return (
    <div>
      <div
        ref={setNodeRef}
        style={{ ...style, paddingLeft: depth * 24 }}
        className={clsx(
          "group flex items-center gap-2 rounded-lg border border-transparent px-2 py-2 hover:border-slate-200 hover:bg-white dark:hover:border-slate-700 dark:hover:bg-slate-800"
        )}
      >
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab touch-none text-slate-300 opacity-0 group-hover:opacity-100 active:cursor-grabbing dark:text-slate-600"
          title="ドラッグして並び替え"
        >
          ⠿
        </button>

        {node.children.length > 0 ? (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="w-4 text-xs text-slate-400"
          >
            {expanded ? "▾" : "▸"}
          </button>
        ) : (
          <span className="w-4" />
        )}

        <select
          value={node.status}
          onChange={(e) => onStatusChange(node.id, e.target.value)}
          className="rounded-md border-none bg-transparent text-xs font-medium focus:ring-1 focus:ring-indigo-400"
          style={statusDef ? { color: statusDef.color } : undefined}
        >
          {statuses.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>

        <span
          className={clsx(
            "flex-1 truncate text-sm",
            isDone && "text-slate-400 line-through"
          )}
        >
          {node.title}
        </span>

        <PriorityBadge priority={node.priority} />

        {node.tags.map((t) => (
          <TagPill key={t.id} tag={t} />
        ))}

        {node.dueDate && (
          <span className={clsx("whitespace-nowrap text-xs", overdue ? "font-semibold text-red-600" : "text-slate-400")}>
            {format(new Date(node.dueDate), "MM/dd")}
          </span>
        )}

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
          <button
            onClick={() => onAddSubtask(node.id)}
            title="サブタスクを追加"
            className="rounded px-1.5 py-0.5 text-xs text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            +サブ
          </button>
          <button
            onClick={() => onEdit(node)}
            title="編集"
            className="rounded px-1.5 py-0.5 text-xs text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            編集
          </button>
          <button
            onClick={() => onDelete(node)}
            title="削除"
            className="rounded px-1.5 py-0.5 text-xs text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30"
          >
            削除
          </button>
        </div>
      </div>

      {expanded && node.children.length > 0 && (
        <SortableContext items={node.children.map((c) => c.id)} strategy={verticalListSortingStrategy}>
          {node.children.map((child) => (
            <TaskNode
              key={child.id}
              node={child}
              depth={depth + 1}
              onStatusChange={onStatusChange}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddSubtask={onAddSubtask}
            />
          ))}
        </SortableContext>
      )}
    </div>
  );
}
