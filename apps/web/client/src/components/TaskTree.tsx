import { useMemo, useRef, useState, type PointerEvent } from "react";
import type { Task } from "../types";
import { buildTaskTree, type TaskTreeNode } from "../utils/tree";
import type { RowDropZone } from "../utils/dnd";
import { TaskNode } from "./TaskNode";
import { TreeDragContext, type TreeDragState } from "./treeDrag";
import { useT } from "../i18n";

interface Props {
  tasks: Task[];
  onStatusChange: (id: string, status: string) => void;
  onEdit: (node: TaskTreeNode) => void;
  onDelete: (node: TaskTreeNode) => void;
  onAddSubtask: (parentId: string) => void;
  onRowDrop?: (activeId: string, targetId: string, zone: RowDropZone) => void;
}

const DRAG_THRESHOLD_PX = 5;
const DROP_EDGE = 0.25; // 行の上下この割合 = 兄弟として挿入、中央 = 子にする

export function TaskTree({ tasks, onStatusChange, onEdit, onDelete, onAddSubtask, onRowDrop }: Props) {
  const t = useT();
  const tree = useMemo(() => buildTaskTree(tasks), [tasks]);
  const [drag, setDrag] = useState<TreeDragState | null>(null);
  const dragRef = useRef<TreeDragState | null>(null);

  const update = (next: TreeDragState | null) => {
    dragRef.current = next;
    setDrag(next);
  };

  // ドラッグ（ハンドルを掴んで動かす）とクリック（行の編集）は、操作する場所で分ける：
  // ドラッグはハンドルだけ。ハンドルはクリックしても編集を開かない。
  const onHandlePointerDown = (id: string, e: PointerEvent<HTMLElement>) => {
    if (e.button !== 0 || !onRowDrop) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    update({ id, startY: e.clientY, moved: false, target: null });
  };

  const onHandlePointerMove = (e: PointerEvent<HTMLElement>) => {
    const cur = dragRef.current;
    if (!cur) return;
    const moved = cur.moved || Math.abs(e.clientY - cur.startY) > DRAG_THRESHOLD_PX;
    if (!moved) return;
    const row = document.elementFromPoint(e.clientX, e.clientY)?.closest<HTMLElement>("[data-row-id]");
    let target: TreeDragState["target"] = null;
    if (row?.dataset.rowId) {
      const rect = row.getBoundingClientRect();
      const frac = (e.clientY - rect.top) / rect.height;
      target = {
        id: row.dataset.rowId,
        zone: frac < DROP_EDGE ? "before" : frac > 1 - DROP_EDGE ? "after" : "child",
      };
    }
    update({ ...cur, moved, target });
  };

  const onHandlePointerUp = () => {
    const cur = dragRef.current;
    update(null);
    if (cur?.moved && cur.target && cur.target.id !== cur.id) {
      onRowDrop?.(cur.id, cur.target.id, cur.target.zone);
    }
  };

  if (tree.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400 dark:border-slate-700">
        {t("タスクがありません。「新しいタスク」から追加してください。")}
      </div>
    );
  }

  return (
    <TreeDragContext.Provider
      value={{ drag, onHandlePointerDown, onHandlePointerMove, onHandlePointerUp, onHandleCancel: () => update(null) }}
    >
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
    </TreeDragContext.Provider>
  );
}
