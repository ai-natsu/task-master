import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
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
    qc.invalidateQueries({ queryKey: ["statuses"] });
    qc.invalidateQueries({ queryKey: ["tasks"] });
    qc.invalidateQueries({ queryKey: ["stats"] });
  };
}

export function useCreateStatus() {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    mutationFn: (data: { label: string; color?: string; isDone?: boolean }) =>
      api.post<StatusDef>("/statuses", data),
    onSuccess: invalidate,
  });
}

export function useUpdateStatus() {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; label?: string; color?: string; isDone?: boolean }) =>
      api.patch<StatusDef>(`/statuses/${id}`, data),
    onSuccess: invalidate,
  });
}

export function useDeleteStatus() {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/statuses/${id}`),
    onSuccess: invalidate,
  });
}

export function useReorderStatuses() {
  const invalidate = useInvalidateStatuses();
  return useMutation({
    mutationFn: (ids: string[]) => api.patch("/statuses/reorder", { ids }),
    onSuccess: invalidate,
  });
}
