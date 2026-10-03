import { Link } from "react-router-dom";
import { format } from "date-fns";
import { useProjects } from "../api/projects";
import { useStats } from "../api/stats";
import { useTasks } from "../api/tasks";
import { useStatuses } from "../api/statuses";
import { Card, StatsCards } from "../components/StatsCards";
import { PriorityBadge } from "../components/Badges";
import { isDueSoon, isOverdue } from "../utils/due";

export function Dashboard() {
  const { data: projects = [] } = useProjects();
  const { data: stats } = useStats();
  const { data: tasks = [] } = useTasks();
  const { data: statuses = [] } = useStatuses();

  const projectNameById = new Map(projects.map((p) => [p.id, p]));
  const doneIds = new Set(statuses.filter((s) => s.isDone).map((s) => s.id));

  const overdue = tasks
    .filter((t) => !doneIds.has(t.status) && t.dueDate && isOverdue(t.dueDate))
    .sort((a, b) => new Date(a.dueDate!).getTime() - new Date(b.dueDate!).getTime())
    .slice(0, 8);

  const upcoming = tasks
    .filter((t) => !doneIds.has(t.status) && t.dueDate && isDueSoon(t.dueDate))
    .sort((a, b) => new Date(a.dueDate!).getTime() - new Date(b.dueDate!).getTime())
    .slice(0, 8);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">ダッシュボード</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card label="プロジェクト数" value={projects.length} />
        <Card label="直近7日の完了" value={stats?.completedLast7Days ?? 0} accent="text-emerald-600" />
      </div>

      {stats && <StatsCards stats={stats} />}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold text-red-600">期限超過のタスク</h3>
          {overdue.length === 0 ? (
            <p className="text-sm text-slate-400">期限超過のタスクはありません</p>
          ) : (
            <ul className="space-y-2">
              {overdue.map((t) => (
                <li key={t.id} className="flex items-center gap-2 text-sm">
                  <PriorityBadge priority={t.priority} />
                  <span className="flex-1 truncate">{t.title}</span>
                  <span className="text-xs text-slate-400">
                    {projectNameById.get(t.projectId)?.name}
                  </span>
                  <span className="text-xs font-medium text-red-600">
                    {format(new Date(t.dueDate!), "MM/dd")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">期限が近いタスク</h3>
          {upcoming.length === 0 ? (
            <p className="text-sm text-slate-400">予定されているタスクはありません</p>
          ) : (
            <ul className="space-y-2">
              {upcoming.map((t) => (
                <li key={t.id} className="flex items-center gap-2 text-sm">
                  <PriorityBadge priority={t.priority} />
                  <span className="flex-1 truncate">{t.title}</span>
                  <span className="text-xs text-slate-400">
                    {projectNameById.get(t.projectId)?.name}
                  </span>
                  <span className="text-xs text-slate-500">
                    {format(new Date(t.dueDate!), "MM/dd")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold">プロジェクト一覧</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-700"
            >
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: p.color }} />
                <span className="font-medium">{p.name}</span>
              </div>
              <div className="mt-2 text-xs text-slate-400">{p._count?.tasks ?? 0} 件のタスク</div>
            </Link>
          ))}
          {projects.length === 0 && (
            <p className="text-sm text-slate-400">まだプロジェクトがありません。サイドバーから作成してください。</p>
          )}
        </div>
      </div>
    </div>
  );
}
