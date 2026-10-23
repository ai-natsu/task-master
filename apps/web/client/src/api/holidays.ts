import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import { inlineMeta, type MutationOpts } from "./meta";
import type { Holiday } from "../types";

export function useHolidays() {
  return useQuery({
    queryKey: ["holidays"],
    queryFn: () => api.get<Holiday[]>("/holidays"),
  });
}

// 日付が一致する行があれば名称を上書きし、無ければ作成する
export function useUpsertHoliday(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (data: { date: string; name: string }) => api.post<Holiday>("/holidays", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}

export function useRenameHoliday(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      api.patch<Holiday>(`/holidays/${id}`, { name }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}

export function useDeleteHoliday(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (id: string) => api.delete(`/holidays/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}

export function useBulkHolidays(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (rows: { date: string; name: string }[]) =>
      api.post<{ count: number }>("/holidays/bulk", { rows }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}
