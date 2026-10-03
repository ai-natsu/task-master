import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { Holiday } from "../types";

export function useHolidays() {
  return useQuery({
    queryKey: ["holidays"],
    queryFn: () => api.get<Holiday[]>("/holidays"),
  });
}

// 日付が一致する行があれば名称を上書きし、無ければ作成する
export function useUpsertHoliday() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { date: string; name: string }) => api.post<Holiday>("/holidays", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}

export function useRenameHoliday() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      api.patch<Holiday>(`/holidays/${id}`, { name }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}

export function useDeleteHoliday() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/holidays/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}

export function useBulkHolidays() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rows: { date: string; name: string }[]) =>
      api.post<{ count: number }>("/holidays/bulk", { rows }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });
}
