import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useProjects } from "../api/projects";
import { useCreateTask, useDeleteTask, useTasks, useUpdateTask } from "../api/tasks";
import { useTags } from "../api/tags";
import { useStats } from "../api/stats";
import { FilterBar, type FilterState } from "../components/FilterBar";
import { TaskTree } from "../components/TaskTree";
import { KanbanBoard } from "../components/KanbanBoard";
import { GanttChart } from "../components/GanttChart";
import { TaskFormModal, taskToFormValue, type TaskFormValue } from "../components/TaskFormModal";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { StatsCards } from "../components/StatsCards";
import { buildTaskTree, flattenWithDepth, type TaskTreeNode } from "../utils/tree";
import type { Task } from "../types";
import { useT } from "../i18n";

export function ProjectView() {
  const t = useT();
  const { projectId } = useParams<{ projectId: string }>();
  const { data: projects = [] } = useProjects();
  const project = projects.find((p) => p.id === projectId);

  const [filters, setFilters] = useState<FilterState>({ search: "" });
  const filtersActive = !!(filters.search || filters.status || filters.priority || filters.tagId);

  const { data: allTasks = [] } = useTasks({ projectId });
  const { data: filteredTasks } = useTasks({ projectId, ...filters });
  const { data: tags = [] } = useTags();
  const { data: stats } = useStats(projectId);

  const tasksToShow = filtersActive ? filteredTasks ?? [] : allTasks;

  const createTask = useCreateTask();
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();

  const [formOpen, setFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>();
  const [newTaskParentId, setNewTaskParentId] = useState<string | null>(null);
  const [deletingTask, setDeletingTask] = useState<TaskTreeNode | undefined>();
  const [showStats, setShowStats] = useState(false);
  const [viewMode, setViewMode] = useState<"tree" | "kanban" | "gantt">("tree");

  const parentOptions = useMemo(() => {
    const tree = buildTaskTree(allTasks);
    return flattenWithDepth(tree).filter((o) => o.id !== editingTask?.id);
  }, [allTasks, editingTask]);

  if (!projectId) return null;

  const openCreate = (parentId: string | null = null) => {
    setEditingTask(undefined);
    setNewTaskParentId(parentId);
    setFormOpen(true);
  };

  const openEdit = (task: Task) => {
    setEditingTask(task);
    setFormOpen(true);
  };

  const handleSubmit = (value: TaskFormValue) => {
    const startDate = value.startDate ? new Date(value.startDate).toISOString() : null;
    const dueDate = value.dueDate ? new Date(value.dueDate).toISOString() : null;
    if (editingTask) {
      updateTask.mutate({
        id: editingTask.id,
        title: value.title,
        description: value.description || null,
        status: value.status || undefined,
        priority: value.priority,
        startDate,
        dueDate,
        tagIds: value.tagIds,
      });
    } else {
      createTask.mutate({
        title: value.title,
        description: value.description || undefined,
        projectId,
        parentId: value.parentId ?? newTaskParentId,
        status: value.status || undefined,
        priority: value.priority,
        startDate,
        dueDate,
        tagIds: value.tagIds,
      });
    }
    setFormOpen(false);
    setEditingTask(undefined);
    setNewTaskParentId(null);
  };

  const handleStatusChange = (id: string, status: string) => {
    updateTask.mutate({ id, status });
  };

  if (!project) {
    return <div className="text-sm text-slate-400">{t("プロジェクトを読み込み中...")}</div>;
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full" style={{ backgroundColor: project.color }} />
            <h1 className="text-xl font-bold">{project.name}</h1>
          </div>
          {project.description && (
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{project.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <div className="flex overflow-hidden rounded-lg border border-slate-300 text-sm font-medium dark:border-slate-600">
            <button
              onClick={() => setViewMode("tree")}
              className={
                viewMode === "tree"
                  ? "bg-indigo-600 px-3 py-1.5 text-white"
                  : "px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
              }
            >
              {t("ツリー")}
            </button>
            <button
              onClick={() => setViewMode("kanban")}
              className={
                viewMode === "kanban"
                  ? "bg-indigo-600 px-3 py-1.5 text-white"
                  : "px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
              }
            >
              {t("カンバン")}
            </button>
            <button
              onClick={() => setViewMode("gantt")}
              className={
                viewMode === "gantt"
                  ? "bg-indigo-600 px-3 py-1.5 text-white"
                  : "px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
              }
            >
              {t("ガント")}
            </button>
          </div>
          <button
            onClick={() => setShowStats((s) => !s)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800"
          >
            {showStats ? t("統計を隠す") : t("統計を表示")}
          </button>
          <button
            onClick={() => openCreate(null)}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {t("+ 新しいタスク")}
          </button>
        </div>
      </div>

      {showStats && stats && (
        <div className="mb-6">
          <StatsCards stats={stats} />
        </div>
      )}

      <div className="mb-4">
        <FilterBar value={filters} onChange={setFilters} tags={tags} />
      </div>

      {viewMode === "tree" ? (
        <TaskTree
          tasks={tasksToShow}
          onStatusChange={handleStatusChange}
          onEdit={openEdit}
          onDelete={setDeletingTask}
          onAddSubtask={openCreate}
        />
      ) : viewMode === "kanban" ? (
        <KanbanBoard tasks={tasksToShow} onEdit={openEdit} />
      ) : (
        <GanttChart
          tasks={tasksToShow}
          onEdit={openEdit}
          onChangeDates={(task, startDate, dueDate) =>
            updateTask.mutate({ id: task.id, startDate, dueDate })
          }
        />
      )}

      <TaskFormModal
        open={formOpen}
        mode={editingTask ? "edit" : "create"}
        initial={editingTask ? taskToFormValue(editingTask) : { parentId: newTaskParentId }}
        parentOptions={parentOptions}
        onSubmit={handleSubmit}
        onClose={() => {
          setFormOpen(false);
          setEditingTask(undefined);
          setNewTaskParentId(null);
        }}
      />

      <ConfirmDialog
        open={!!deletingTask}
        title={t("タスクを削除")}
        message={t("「{name}」を削除すると、サブタスクも削除されます。よろしいですか？", {
          name: deletingTask?.title ?? "",
        })}
        onConfirm={() => {
          if (deletingTask) deleteTask.mutate(deletingTask.id);
          setDeletingTask(undefined);
        }}
        onCancel={() => setDeletingTask(undefined)}
      />
    </div>
  );
}
