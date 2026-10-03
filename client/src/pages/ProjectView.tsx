import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useProjects } from "../api/projects";
import { useCreateTask, useDeleteTask, useMoveTask, useReorderTasks, useTasks, useUpdateTask } from "../api/tasks";
import { useTags } from "../api/tags";
import { useStats } from "../api/stats";
import { FilterBar, type FilterState } from "../components/FilterBar";
import { TaskTree } from "../components/TaskTree";
import { KanbanBoard } from "../components/KanbanBoard";
import { GanttChart } from "../components/GanttChart";
import { TaskFormModal, taskToFormValue, type TaskFormValue } from "../components/TaskFormModal";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { StatsCards } from "../components/StatsCards";
import { PaperTabs } from "../components/PaperTabs";
import { errorMessage } from "../utils/errorMessage";
import { buildTaskTree, descendantIds, flattenWithDepth, type TaskTreeNode } from "../utils/tree";
import { planRowDrop, type RowDropZone } from "../utils/dnd";
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
  const reorderTasks = useReorderTasks();
  // フォーム（モーダル）からの保存は、失敗をモーダル内に表示する（inline）
  const formCreateTask = useCreateTask({ inline: true });
  const formUpdateTask = useUpdateTask({ inline: true });
  const formMoveTask = useMoveTask({ inline: true });
  const [formError, setFormError] = useState("");
  const deleteTask = useDeleteTask();

  const [formOpen, setFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>();
  const [newTaskParentId, setNewTaskParentId] = useState<string | null>(null);
  const [deletingTask, setDeletingTask] = useState<TaskTreeNode | undefined>();
  const [showStats, setShowStats] = useState(false);
  const [viewMode, setViewMode] = useState<"tree" | "kanban" | "gantt">("tree");

  const parentOptions = useMemo(() => {
    const tree = buildTaskTree(allTasks);
    // 自分自身とその子孫は親にできない（循環の防止）
    const excluded = editingTask ? descendantIds(allTasks, editingTask.id) : new Set<string>();
    return flattenWithDepth(tree).filter((o) => o.id !== editingTask?.id && !excluded.has(o.id));
  }, [allTasks, editingTask]);

  if (!projectId) return null;

  const openCreate = (parentId: string | null = null) => {
    setEditingTask(undefined);
    setNewTaskParentId(parentId);
    setFormError("");
    setFormOpen(true);
  };

  const openEdit = (task: Task) => {
    setEditingTask(task);
    setFormError("");
    setFormOpen(true);
  };

  const handleSubmit = async (value: TaskFormValue) => {
    const startDate = value.startDate ? new Date(value.startDate).toISOString() : null;
    const dueDate = value.dueDate ? new Date(value.dueDate).toISOString() : null;
    setFormError("");
    try {
      if (editingTask) {
        await formUpdateTask.mutateAsync({
          id: editingTask.id,
          title: value.title,
          description: value.description || null,
          status: value.status || undefined,
          priority: value.priority,
          startDate,
          dueDate,
          tagIds: value.tagIds,
        });
        if (value.parentId !== editingTask.parentId) {
          // 親タスクを変えた場合は、新しい親の最後の子として付け替える
          const siblings = allTasks.filter((t) => t.parentId === value.parentId && t.id !== editingTask.id);
          const order = siblings.reduce((max, t) => Math.max(max, t.order), -1) + 1;
          await formMoveTask.mutateAsync({ id: editingTask.id, parentId: value.parentId, order });
        }
      } else {
        await formCreateTask.mutateAsync({
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
    } catch (e) {
      // 失敗したらモーダルを閉じず、理由をモーダル内に表示する
      setFormError(errorMessage(e, t));
      return;
    }
    setFormOpen(false);
    setEditingTask(undefined);
    setNewTaskParentId(null);
  };

  // ツリー・ガントの行ドラッグ（並べ替え・親の付け替え）。フィルタ中でも全タスクを基準に計画する
  const handleRowDrop = (activeId: string, targetId: string, zone: RowDropZone) => {
    const plan = planRowDrop(allTasks, activeId, targetId, zone);
    if (plan.reorder) reorderTasks.mutate(plan.reorder);
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
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowStats((s) => !s)}
            className="rounded-lg px-3 py-1.5 text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-800"
          >
            {showStats ? t("統計を隠す") : t("統計を表示")}
          </button>
          <PaperTabs
            value={viewMode}
            onChange={setViewMode}
            tabs={[
              { key: "tree", label: t("ツリー") },
              { key: "kanban", label: t("カンバン") },
              { key: "gantt", label: t("ガント") },
            ]}
          />
          <button
            onClick={() => openCreate(null)}
            className="rounded-lg bg-indigo-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-600"
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
          onRowDrop={handleRowDrop}
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
          onRowDrop={handleRowDrop}
        />
      )}

      <TaskFormModal
        open={formOpen}
        mode={editingTask ? "edit" : "create"}
        initial={editingTask ? taskToFormValue(editingTask) : { parentId: newTaskParentId }}
        parentOptions={parentOptions}
        error={formError}
        onSubmit={handleSubmit}
        onClose={() => {
          setFormOpen(false);
          setEditingTask(undefined);
          setFormError("");
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
