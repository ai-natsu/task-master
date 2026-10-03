import { useMemo, useState, type PointerEvent } from "react";
import clsx from "clsx";
import { differenceInCalendarDays, format, isSameDay, startOfDay } from "date-fns";
import type { Task } from "../types";
import { buildTaskTree, flattenNodes } from "../utils/tree";
import {
  applyGanttDrag,
  barToDates,
  computeBar,
  computeMonths,
  computeRange,
  type GanttDragMode,
} from "../utils/gantt";
import { useStatuses } from "../api/statuses";
import { useT } from "../i18n";

const DAY_W = 28;
const ROW_H = 36;
const LABEL_W = 220;
const EDGE_W = 6; // バー端のリサイズ用つかみ幅(px)

interface Props {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onChangeDates?: (task: Task, startDate: string, dueDate: string) => void;
}

interface DragState {
  id: string;
  mode: GanttDragMode;
  startX: number;
  deltaDays: number;
}

function dragModeAt(e: PointerEvent<HTMLDivElement>): GanttDragMode {
  const rect = e.currentTarget.getBoundingClientRect();
  const x = e.clientX - rect.left;
  if (x <= EDGE_W) return "resize-start";
  if (x >= rect.width - EDGE_W) return "resize-end";
  return "move";
}

export function GanttChart({ tasks, onEdit, onChangeDates }: Props) {
  const t = useT();
  const [drag, setDrag] = useState<DragState | null>(null);
  const { data: statuses = [] } = useStatuses();
  const statusById = useMemo(() => new Map(statuses.map((s) => [s.id, s])), [statuses]);

  const rows = useMemo(() => flattenNodes(buildTaskTree(tasks)), [tasks]);

  const today = startOfDay(new Date());
  const { days, rangeStart } = useMemo(
    () => computeRange(rows.map((r) => r.node), today),
    [rows, today.getTime()]
  );
  const todayOffset = differenceInCalendarDays(today, rangeStart);
  const months = useMemo(() => computeMonths(days, t("yyyy年M月")), [days, t]);

  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400 dark:border-slate-700">
        {t("タスクがありません。")}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div style={{ width: LABEL_W + days.length * DAY_W }}>
        {/* 月ヘッダー */}
        <div className="flex border-b border-slate-200 text-xs font-medium text-slate-500 dark:border-slate-700">
          <div
            className="sticky left-0 z-20 shrink-0 border-r border-slate-200 bg-white px-3 py-1.5 dark:border-slate-700 dark:bg-slate-900"
            style={{ width: LABEL_W }}
          >
            {t("タスク")}
          </div>
          {months.map((m, i) => (
            <div
              key={i}
              className="shrink-0 border-r border-slate-200 px-2 py-1.5 dark:border-slate-700"
              style={{ width: m.count * DAY_W }}
            >
              {m.label}
            </div>
          ))}
        </div>

        {/* 日ヘッダー */}
        <div className="flex border-b border-slate-200 text-[10px] text-slate-400 dark:border-slate-700">
          <div
            className="sticky left-0 z-20 shrink-0 border-r border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900"
            style={{ width: LABEL_W }}
          />
          {days.map((d) => {
            const dow = d.getDay();
            return (
              <div
                key={d.toISOString()}
                className={clsx(
                  "shrink-0 py-1 text-center",
                  dow === 0 && "bg-red-50 text-red-400 dark:bg-red-950/30",
                  dow === 6 && "bg-blue-50 text-blue-400 dark:bg-blue-950/30",
                  isSameDay(d, today) && "bg-amber-100 font-bold text-amber-700 dark:bg-amber-900/40"
                )}
                style={{ width: DAY_W }}
              >
                {format(d, "d")}
              </div>
            );
          })}
        </div>

        {/* タスク行 */}
        {rows.map(({ node, depth }) => {
          const statusDef = statusById.get(node.status);
          const baseBar = computeBar(node, rangeStart);
          const bar =
            baseBar && drag?.id === node.id
              ? applyGanttDrag(baseBar, drag.mode, drag.deltaDays)
              : baseBar;
          const left = bar ? bar.offsetDays * DAY_W : 0;
          const width = bar ? bar.spanDays * DAY_W - 4 : 0;

          return (
            <div
              key={node.id}
              className="flex border-b border-slate-100 last:border-b-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
              style={{ height: ROW_H }}
            >
              <button
                onDoubleClick={() => onEdit(node)}
                className="sticky left-0 z-10 flex shrink-0 items-center gap-1.5 truncate border-r border-slate-200 bg-white px-3 text-left text-sm hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-900 dark:hover:text-indigo-400"
                style={{ width: LABEL_W, paddingLeft: 12 + depth * 16 }}
                title={`${node.title}\n${t("ダブルクリックで編集")}`}
              >
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: statusDef?.color ?? "#94a3b8" }}
                />
                <span className={clsx("truncate", statusDef?.isDone && "text-slate-400 line-through")}>
                  {node.title}
                </span>
              </button>

              <div
                className="relative shrink-0"
                style={{
                  width: days.length * DAY_W,
                  backgroundImage: `repeating-linear-gradient(to right, transparent 0 ${DAY_W - 1}px, rgba(148,163,184,0.18) ${DAY_W - 1}px ${DAY_W}px)`,
                }}
              >
                {todayOffset >= 0 && todayOffset < days.length && (
                  <div
                    className="absolute bottom-0 top-0 w-px bg-amber-400/70"
                    style={{ left: todayOffset * DAY_W + DAY_W / 2 }}
                  />
                )}
                {bar && (
                  <div
                    onDoubleClick={() => onEdit(node)}
                    onPointerDown={(e) => {
                      if (e.button !== 0 || !onChangeDates) return;
                      e.currentTarget.setPointerCapture(e.pointerId);
                      setDrag({ id: node.id, mode: dragModeAt(e), startX: e.clientX, deltaDays: 0 });
                    }}
                    onPointerMove={(e) => {
                      if (drag?.id === node.id) {
                        const deltaDays = Math.round((e.clientX - drag.startX) / DAY_W);
                        if (deltaDays !== drag.deltaDays) setDrag({ ...drag, deltaDays });
                      } else {
                        e.currentTarget.style.cursor = dragModeAt(e) === "move" ? "grab" : "ew-resize";
                      }
                    }}
                    onPointerUp={() => {
                      if (drag?.id === node.id && drag.deltaDays !== 0 && baseBar) {
                        const next = applyGanttDrag(baseBar, drag.mode, drag.deltaDays);
                        const dates = barToDates(next, rangeStart);
                        onChangeDates?.(node, dates.startDate, dates.dueDate);
                      }
                      setDrag(null);
                    }}
                    onPointerCancel={() => setDrag(null)}
                    className={clsx(
                      "absolute top-1/2 h-4 -translate-y-1/2 touch-none select-none rounded-full shadow-sm hover:opacity-80",
                      statusDef?.isDone && "opacity-50"
                    )}
                    style={{
                      left: left + 2,
                      width: Math.max(width, DAY_W - 4),
                      backgroundColor: statusDef?.color ?? "#6366f1",
                    }}
                    title={`${node.title}\n${node.startDate ? format(new Date(node.startDate), "MM/dd") : "?"} 〜 ${node.dueDate ? format(new Date(node.dueDate), "MM/dd") : "?"}`}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>

      <p className="border-t border-slate-200 px-3 py-2 text-xs text-slate-400 dark:border-slate-700">
        {t("バーは開始日〜期限の期間を表します（片方のみ設定の場合は1日分）。開始日・期限が未設定のタスクはバー非表示。バーを左右にドラッグして日程を移動、両端のドラッグで期間を変更できます。バーまたはタスク名のダブルクリックで編集できます。")}
      </p>
    </div>
  );
}
