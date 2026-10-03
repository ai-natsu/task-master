import type { ReactNode } from "react";
import type { Stats } from "../types";
import { PRIORITIES, PRIORITY_COLORS, PRIORITY_LABELS } from "../types";
import { useStatuses } from "../api/statuses";
import { StatusBadge } from "./Badges";

export function Card({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs font-medium text-slate-400">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${accent ?? ""}`}>{value}</div>
    </div>
  );
}

function BarRow({ chip, count, total }: { chip: ReactNode; count: number; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 text-center">{chip}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 shrink-0 text-right text-xs text-slate-400">{count}</span>
    </div>
  );
}

export function StatsCards({ stats }: { stats: Stats }) {
  const { data: statuses = [] } = useStatuses();

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card label="タスク総数" value={stats.total} />
        <Card label="完了率" value={`${stats.completionRate}%`} accent="text-emerald-600" />
        <Card label="期限超過" value={stats.overdue} accent={stats.overdue > 0 ? "text-red-600" : ""} />
        <Card label="期限が近い（3日後まで）" value={stats.dueSoon} accent="text-amber-600" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">ステータス別</h3>
          <div className="space-y-2">
            {statuses.map((s) => (
              <BarRow
                key={s.id}
                chip={<StatusBadge status={s} />}
                count={stats.byStatus[s.id] ?? 0}
                total={stats.total}
              />
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">優先度別</h3>
          <div className="space-y-2">
            {[...PRIORITIES].reverse().map((p) => (
              <BarRow
                key={p}
                chip={
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[p]}`}>
                    {PRIORITY_LABELS[p]}
                  </span>
                }
                count={stats.byPriority[p] ?? 0}
                total={stats.total}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
