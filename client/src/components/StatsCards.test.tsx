import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { StatsCards } from "./StatsCards";
import type { Stats } from "../types";

// Mock the statuses hook so StatsCards has a known set of statuses.
vi.mock("../api/statuses", () => ({
  useStatuses: () => ({
    data: [
      { id: "TODO", label: "未着手", color: "#64748b", order: 0, isDone: false },
      { id: "DONE", label: "完了", color: "#10b981", order: 1, isDone: true },
    ],
  }),
}));

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const stats: Stats = {
  total: 10,
  byStatus: { TODO: 6, DONE: 4 },
  byPriority: { LOW: 1, MEDIUM: 2, HIGH: 3, URGENT: 4 },
  overdue: 2,
  dueSoon: 1,
  completedLast7Days: 4,
  completionRate: 40,
};

describe("StatsCards", () => {
  beforeEach(() => {
    render(<StatsCards stats={stats} />, { wrapper });
  });

  it("V-2: renders priority rows in descending order (緊急→高→中→低)", () => {
    const priorityCard = screen.getByText("優先度別").closest("div")!;
    // Leaf spans only (the badge labels), to avoid double-counting wrapper spans.
    const labels = Array.from(priorityCard.querySelectorAll("span"))
      .filter((s) => s.children.length === 0)
      .map((s) => s.textContent)
      .filter((t) => ["緊急", "高", "中", "低"].includes(t ?? ""));
    expect(labels).toEqual(["緊急", "高", "中", "低"]);
  });

  it("shows completion rate and totals", () => {
    expect(screen.getByText("40%")).toBeInTheDocument();
    expect(screen.getByText("タスク総数")).toBeInTheDocument();
  });
});
