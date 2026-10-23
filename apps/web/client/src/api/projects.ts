import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import { inlineMeta, type MutationOpts } from "./meta";
import type { Project } from "../types";

export function useProjects(includeArchived = false) {
  return useQuery({
    queryKey: ["projects", { includeArchived }],
    queryFn: () =>
      api.get<Project[]>(`/projects${includeArchived ? "?includeArchived=true" : ""}`),
  });
}

export function useCreateProject(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (data: { name: string; description?: string; color?: string }) =>
      api.post<Project>("/projects", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: ({ id, ...data }: { id: string; name?: string; description?: string; color?: string; archived?: boolean }) =>
      api.patch<Project>(`/projects/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${id}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["projects"] });
      void qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useReorderProjects() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ids: string[]) => api.patch("/projects/reorder", { ids }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}
