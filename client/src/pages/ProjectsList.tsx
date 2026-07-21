import { useState } from "react";
import { Link } from "react-router-dom";
import clsx from "clsx";
import { useCreateProject, useDeleteProject, useProjects, useUpdateProject } from "../api/projects";
import { ProjectFormModal, type ProjectFormValue } from "../components/ProjectFormModal";
import { ConfirmDialog } from "../components/ConfirmDialog";
import type { Project } from "../types";

export function ProjectsList() {
  const [showArchived, setShowArchived] = useState(false);
  const { data: projects = [] } = useProjects(showArchived);
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Project | undefined>();
  const [deleting, setDeleting] = useState<Project | undefined>();
  const [archiving, setArchiving] = useState<Project | undefined>();

  const handleSubmit = (value: ProjectFormValue) => {
    if (editing) {
      updateProject.mutate({ id: editing.id, ...value });
    } else {
      createProject.mutate(value);
    }
    setFormOpen(false);
    setEditing(undefined);
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">プロジェクト一覧</h1>
        <button
          onClick={() => {
            setEditing(undefined);
            setFormOpen(true);
          }}
          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          + 新しいプロジェクト
        </button>
      </div>

      <label className="mb-4 flex w-fit items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
        <input
          type="checkbox"
          checked={showArchived}
          onChange={(e) => setShowArchived(e.target.checked)}
          className="rounded"
        />
        アーカイブ済みも表示
      </label>

      <div className="space-y-2">
        {projects.map((p) => (
          <div
            key={p.id}
            className={clsx(
              "flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900",
              p.archived && "opacity-60"
            )}
          >
            <span className="h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: p.color }} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Link
                  to={`/projects/${p.id}`}
                  className="truncate font-medium hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                  {p.name}
                </Link>
                {p.archived && (
                  <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                    アーカイブ済み
                  </span>
                )}
              </div>
              {p.description && (
                <p className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">{p.description}</p>
              )}
            </div>
            <span className="shrink-0 text-xs text-slate-400">{p._count?.tasks ?? 0} 件のタスク</span>
            <div className="flex shrink-0 gap-1">
              <button
                onClick={() => {
                  setEditing(p);
                  setFormOpen(true);
                }}
                className="rounded-lg px-2 py-1 text-xs font-medium hover:bg-slate-100 dark:hover:bg-slate-700"
              >
                編集
              </button>
              <button
                onClick={() => setArchiving(p)}
                className="rounded-lg px-2 py-1 text-xs font-medium text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/30"
              >
                {p.archived ? "復元" : "アーカイブ"}
              </button>
              <button
                onClick={() => setDeleting(p)}
                className="rounded-lg px-2 py-1 text-xs font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30"
              >
                削除
              </button>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400 dark:border-slate-700">
            プロジェクトがありません。「+ 新しいプロジェクト」から作成してください。
          </div>
        )}
      </div>

      <ProjectFormModal
        open={formOpen}
        mode={editing ? "edit" : "create"}
        initial={editing}
        onSubmit={handleSubmit}
        onClose={() => {
          setFormOpen(false);
          setEditing(undefined);
        }}
      />

      <ConfirmDialog
        open={!!deleting}
        title="プロジェクトを削除"
        message={`「${deleting?.name}」を削除すると、含まれるすべてのタスクも削除されます。よろしいですか？`}
        onConfirm={() => {
          if (deleting) deleteProject.mutate(deleting.id);
          setDeleting(undefined);
        }}
        onCancel={() => setDeleting(undefined)}
      />

      <ConfirmDialog
        open={!!archiving}
        title={archiving?.archived ? "プロジェクトを復元" : "プロジェクトをアーカイブ"}
        message={
          archiving?.archived
            ? `「${archiving?.name}」を復元しますか？一覧に再表示されます。`
            : `「${archiving?.name}」をアーカイブしますか？一覧では非表示になります（「アーカイブ済みも表示」で再表示できます）。`
        }
        confirmLabel={archiving?.archived ? "復元する" : "アーカイブする"}
        danger={false}
        onConfirm={() => {
          if (archiving) updateProject.mutate({ id: archiving.id, archived: !archiving.archived });
          setArchiving(undefined);
        }}
        onCancel={() => setArchiving(undefined)}
      />
    </div>
  );
}
