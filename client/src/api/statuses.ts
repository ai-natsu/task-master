import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import { inlineMeta, type MutationOpts } from "./meta";
import type { StatusDef } from "../types";

export function useStatuses() {
  return useQuery({
    queryKey: ["statuses"],
    queryFn: () => api.get<StatusDef[]>("/statuses"),
    staleTime: 60_000,
  });
}

function useInvalidateStatuses() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: ["statuses"] });
    void qc.invalidateQueries({ queryKey: ["tasks"] });
    void qc.invalidateQueries({ queryKey: ["stats"] });
  };
}

export function useCreateStatus(opts?: MutationOpts) {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (data: { label: string; color?: string; isDone?: boolean }) =>
      api.post<StatusDef>("/statuses", data),
    onSuccess: invalidate,
  });
}

export function useUpdateStatus(opts?: MutationOpts) {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: ({ id, ...data }: { id: string; label?: string; color?: string; isDone?: boolean }) =>
      api.patch<StatusDef>(`/statuses/${id}`, data),
    onSuccess: invalidate,
  });
}

export function useDeleteStatus(opts?: MutationOpts) {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (id: string) => api.delete(`/statuses/${id}`),
    onSuccess: invalidate,
  });
}

export function useReorderStatuses(opts?: MutationOpts) {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (ids: string[]) => api.patch("/statuses/reorder", { ids }),
    onSuccess: invalidate,
  });
}
