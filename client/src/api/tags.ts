import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import { inlineMeta, type MutationOpts } from "./meta";
import type { Tag } from "../types";

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: () => api.get<Tag[]>("/tags"),
  });
}

export function useCreateTag(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (data: { name: string; color?: string }) => api.post<Tag>("/tags", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags"] }),
  });
}

export function useDeleteTag(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: (id: string) => api.delete(`/tags/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tags"] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useUpdateTag(opts?: MutationOpts) {
  const qc = useQueryClient();
  return useMutation({
    meta: inlineMeta(opts),
    mutationFn: ({ id, ...data }: { id: string; name?: string; color?: string }) =>
      api.patch<Tag>(`/tags/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tags"] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
