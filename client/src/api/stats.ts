import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { Stats } from "../types";

export function useStats(projectId?: string) {
  return useQuery({
    queryKey: ["stats", projectId],
    queryFn: () => api.get<Stats>(`/stats${projectId ? `?projectId=${projectId}` : ""}`),
    refetchInterval: 30_000,
  });
}
