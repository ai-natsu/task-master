import { useState } from "react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";
import { useCreateProject, useDeleteProject, useProjects, useUpdateProject } from "../api/projects";
import { ProjectFormModal, type ProjectFormValue } from "./ProjectFormModal";
import { ConfirmDialog } from "./ConfirmDialog";
import type { Project } from "../types";
import { useT } from "../i18n";

export function Sidebar() {
  const t = useT();
  const { data: projects = [] } = useProjects();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Project | undefined>();
  const [deleting, setDeleting] = useState<Project | undefined>();

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
    <aside className="flex h-screen w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-4 dark:border-slate-800">
        <span className="text-lg font-bold text-indigo-600">✓ TaskMaster</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            clsx(
              "mb-2 flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium",
              isActive ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300" : "hover:bg-slate-100 dark:hover:bg-slate-800"
            )
          }
        >
          {t("📊 ダッシュボード")}
        </NavLink>

        <NavLink
          to="/projects"
          end
          className={({ isActive }) =>
            clsx(
              "mb-2 flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium",
              isActive ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300" : "hover:bg-slate-100 dark:hover:bg-slate-800"
            )
          }
        >
          {t("📁 プロジェクト一覧")}
        </NavLink>

        <div className="mb-1 mt-3 px-3">
          <span className="text-xs font-semibold uppercase text-slate-400">{t("プロジェクト一覧")}</span>
        </div>

        {projects.map((p) => (
          <div key={p.id} className="group flex items-center gap-1">
            <NavLink
              to={`/projects/${p.id}`}
              className={({ isActive }) =>
                clsx(
                  "flex flex-1 items-center gap-2 truncate rounded-lg px-3 py-2 text-sm font-medium",
                  isActive
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"
                    : "hover:bg-slate-100 dark:hover:bg-slate-800"
                )
              }
            >
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: p.color }} />
              <span className="truncate">{p.name}</span>
              <span className="ml-auto shrink-0 text-xs text-slate-400">{p._count?.tasks ?? 0}</span>
            </NavLink>
            <div className="hidden shrink-0 group-hover:flex">
              <button
                onClick={() => {
                  setEditing(p);
                  setFormOpen(true);
                }}
                className="rounded px-1 text-xs text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
              >
                ✎
              </button>
              <button
                onClick={() => setDeleting(p)}
                className="rounded px-1 text-xs text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-200 px-2 py-2 dark:border-slate-800">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            clsx(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium",
              isActive
                ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"
                : "hover:bg-slate-100 dark:hover:bg-slate-800"
            )
          }
        >
          {t("⚙️ 設定")}
        </NavLink>
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
        title={t("プロジェクトを削除")}
        message={t("「{name}」を削除すると、含まれるすべてのタスクも削除されます。よろしいですか？", {
          name: deleting?.name ?? "",
        })}
        onConfirm={() => {
          if (deleting) deleteProject.mutate(deleting.id);
          setDeleting(undefined);
        }}
        onCancel={() => setDeleting(undefined)}
      />
    </aside>
  );
}
