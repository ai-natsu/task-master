export const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"] as const;

export type Priority = (typeof PRIORITIES)[number];

export interface StatusDef {
  id: string;
  label: string;
  color: string;
  order: number;
  isDone: boolean;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
  /** このタグが付いているタスクの件数（GET /api/tags のみ） */
  _count?: { tasks: number };
}

export interface Holiday {
  id: string;
  date: string; // YYYY-MM-DD
  name: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  color: string;
  archived: boolean;
  order: number;
  createdAt: string;
  updatedAt: string;
  _count?: { tasks: number };
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: Priority;
  startDate: string | null;
  dueDate: string | null;
  order: number;
  projectId: string;
  parentId: string | null;
  createdAt: string;
  updatedAt: string;
  tags: Tag[];
}

export interface Stats {
  total: number;
  byStatus: Record<string, number>;
  byPriority: Record<Priority, number>;
  overdue: number;
  dueSoon: number;
  completedLast7Days: number;
  completionRate: number;
}

export const PRIORITY_LABELS: Record<Priority, string> = {
  LOW: "低",
  MEDIUM: "中",
  HIGH: "高",
  URGENT: "緊急",
};

export const PRIORITY_COLORS: Record<Priority, string> = {
  LOW: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  MEDIUM: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200",
  HIGH: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  URGENT: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200",
};
