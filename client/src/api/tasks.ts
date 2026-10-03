import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import { inlineMeta, type MutationOpts } from "./meta";
import type { Priority, Task } from "../types";

export interface TaskFilters {
  projectId?: string;
  status?: string;
  priority?: Priority;
  tagId?: string;
  search?: string;
}

function buildQuery(filters: TaskFilters) {
  const params = new URLSearchParams();
  if (filters.projectId) params.set("projectId", filters.projectId);
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.tagId) params.set("tagId", filters.tagId);
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function useTasks(filters: TaskFilters = {}) {
  return useQuery({
    queryKey: ["tasks", filters],
    queryFn: () => api.get<Task[]>(`/tasks${buildQuery(filters)}`),
  });
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  projectId: string;
  parentId?: string | null;
  status?: string;
  priority?: Priority;
  startDate?: string | null;
  dueDate?: string | null;
  tagIds?: string[];
}

export function useCreateTask(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (data: CreateTaskInput) => api.post<Task>("/tasks", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export interface UpdateTaskInput {
  id: string;
  title?: string;
  description?: string | null;
  status?: string;
  priority?: Priority;
  startDate?: string | null;
  dueDate?: string | null;
  tagIds?: string[];
}

export function useUpdateTask(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: ({ id, ...data }: UpdateTaskInput) => api.patch<Task>(`/tasks/${id}`, data),
    onMutate: async (updated) => {
      await qc.cancelQueries({ queryKey: ["tasks"] });
      const previous = qc.getQueriesData<Task[]>({ queryKey: ["tasks"] });
      qc.setQueriesData<Task[]>({ queryKey: ["tasks"] }, (old) =>
        old?.map((t) => (t.id === updated.id ? { ...t, ...updated } : t))
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      context?.previous.forEach(([key, data]) => qc.setQueryData(key, data));
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/tasks/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useMoveTask(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: ({ id, parentId, projectId, order }: { id: string; parentId?: string | null; projectId?: string; order?: number }) =>
      api.patch<Task>(`/tasks/${id}/move`, { parentId, projectId, order }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useReorderTasks() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (items: { id: string; order: number; parentId?: string | null; projectId?: string }[]) =>
      api.patch("/tasks/reorder", { items }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}
