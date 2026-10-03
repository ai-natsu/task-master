import { useState } from "react";
import clsx from "clsx";
import { isOverdue } from "../utils/due";
import type { TaskTreeNode } from "../utils/tree";
import { useStatuses } from "../api/statuses";
import { PriorityBadge, TagList } from "./Badges";
import { useFormatDate, useT } from "../i18n";
import { useTreeDrag } from "./treeDrag";

interface Props {
  node: TaskTreeNode;
  depth: number;
  onStatusChange: (id: string, status: string) => void;
  onEdit: (node: TaskTreeNode) => void;
  onDelete: (node: TaskTreeNode) => void;
  onAddSubtask: (parentId: string) => void;
}

export function TaskNode({ node, depth, onStatusChange, onEdit, onDelete, onAddSubtask }: Props) {
  const t = useT();
  const formatDate = useFormatDate();
  const [expanded, setExpanded] = useState(true);
  const { data: statuses = [] } = useStatuses();
  const { drag, onHandlePointerDown, onHandlePointerMove, onHandlePointerUp, onHandleCancel } = useTreeDrag();
  const isDragging = drag?.moved === true && drag.id === node.id;
  // ドロップ先の行には、挿入位置（上端=直前、下端=直後）または「子にする」枠を表示する
  const dropZone = drag?.moved && drag.target?.id === node.id && drag.id !== node.id ? drag.target.zone : null;

  const statusDef = statuses.find((s) => s.id === node.status);
  const isDone = statusDef?.isDone ?? false;
  const overdue = node.dueDate && !isDone && isOverdue(node.dueDate);

  return (
    <div>
      <div
        data-row-id={node.id}
        onClick={(e) => {
          // 行内のボタン・セレクト上のクリックは編集を開かない（それぞれの操作を優先）
          if ((e.target as HTMLElement).closest("button, select")) return;
          onEdit(node);
        }}
        style={{ paddingLeft: depth * 24 }}
        className={clsx(
          "group flex items-center gap-2 rounded-lg border border-transparent px-2 py-2 hover:border-slate-200 hover:bg-white dark:hover:border-slate-700 dark:hover:bg-slate-800",
          isDragging && "opacity-50",
          dropZone === "before" && "shadow-[inset_0_3px_0_0_#6366f1]",
          dropZone === "after" && "shadow-[inset_0_-3px_0_0_#6366f1]",
          dropZone === "child" && "ring-2 ring-inset ring-indigo-500"
        )}
      >
        <button
          onPointerDown={(e) => onHandlePointerDown(node.id, e)}
          onPointerMove={onHandlePointerMove}
          onPointerUp={onHandlePointerUp}
          onPointerCancel={onHandleCancel}
          className="cursor-grab touch-none text-slate-300 opacity-0 group-hover:opacity-100 active:cursor-grabbing dark:text-slate-600"
          title={t("ドラッグして並び替え")}
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

        {/* V2 の表と同じ項目・並び順：タスク名 → ステータス → 優先度 → 開始日 → 期限 → タグ */}
        <span
          className={clsx("flex-1 truncate text-sm", isDone && "text-slate-400 line-through")}
          title={node.title}
        >
          {node.title}
        </span>

        <select
          value={node.status}
          onChange={(e) => onStatusChange(node.id, e.target.value)}
          className="w-24 shrink-0 rounded-md border-none bg-transparent text-xs font-medium focus:ring-1 focus:ring-indigo-400"
          style={statusDef ? { color: statusDef.color } : undefined}
        >
          {statuses.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>

        <span className="flex w-12 shrink-0 justify-center">
          <PriorityBadge priority={node.priority} />
        </span>

        <span className="w-28 shrink-0 whitespace-nowrap text-center text-xs text-slate-400">
          {node.startDate ? formatDate(node.startDate) : ""}
        </span>

        <span
          className={clsx(
            "w-28 shrink-0 whitespace-nowrap text-center text-xs",
            overdue ? "font-semibold text-red-600" : "text-slate-400"
          )}
        >
          {node.dueDate ? formatDate(node.dueDate) : ""}
        </span>

        <span className="flex w-40 shrink-0 items-center gap-1 overflow-hidden">
          <TagList tags={node.tags} />
        </span>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
          <button
            onClick={() => onAddSubtask(node.id)}
            title={t("サブタスクを追加")}
            className="rounded px-1.5 py-0.5 text-xs text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            {t("+サブ")}
          </button>
          <button
            onClick={() => onEdit(node)}
            title={t("編集")}
            className="rounded px-1.5 py-0.5 text-xs text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            {t("編集")}
          </button>
          <button
            onClick={() => onDelete(node)}
            title={t("削除")}
            className="rounded px-1.5 py-0.5 text-xs text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30"
          >
            {t("削除")}
          </button>
        </div>
      </div>

      {expanded && node.children.length > 0 && (
        <>
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
        </>
      )}
    </div>
  );
}
