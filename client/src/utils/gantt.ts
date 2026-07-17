import { addDays, differenceInCalendarDays, format, startOfDay } from "date-fns";
import type { Task } from "../types";

/**
 * Date-grid calculations for the Gantt chart, kept pure so they can be unit
 * tested without rendering. The component supplies `today` explicitly rather
 * than reading the clock here, which keeps these functions deterministic.
 */

export interface GanttRange {
  rangeStart: Date;
  days: Date[];
}

/**
 * The visible date range: spans every task's start/due date and always
 * includes today, padded by 3 days before and 7 after. With no dated tasks it
 * falls back to a two-week window from today.
 */
export function computeRange(tasks: Pick<Task, "startDate" | "dueDate">[], today: Date): GanttRange {
  const base = startOfDay(today);
  const dates: Date[] = [];
  for (const t of tasks) {
    if (t.startDate) dates.push(startOfDay(new Date(t.startDate)));
    if (t.dueDate) dates.push(startOfDay(new Date(t.dueDate)));
  }

  let min = dates.length ? new Date(Math.min(...dates.map((d) => d.getTime()))) : base;
  let max = dates.length ? new Date(Math.max(...dates.map((d) => d.getTime()))) : addDays(base, 13);
  if (base < min) min = base;
  if (base > max) max = base;
  min = addDays(min, -3);
  max = addDays(max, 7);

  const count = differenceInCalendarDays(max, min) + 1;
  return { rangeStart: min, days: Array.from({ length: count }, (_, i) => addDays(min, i)) };
}

export interface GanttBar {
  /** Offset in days from the range start. */
  offsetDays: number;
  /** Inclusive span in days (1 when only one of start/due is set). */
  spanDays: number;
}

/**
 * Bar geometry for one task, in days. Returns null when neither date is set,
 * meaning no bar is drawn. A single date yields a one-day bar.
 */
export function computeBar(
  task: Pick<Task, "startDate" | "dueDate">,
  rangeStart: Date
): GanttBar | null {
  const start = task.startDate ? startOfDay(new Date(task.startDate)) : null;
  const due = task.dueDate ? startOfDay(new Date(task.dueDate)) : null;
  const barStart = start ?? due;
  const barEnd = due ?? start;
  if (!barStart || !barEnd) return null;

  return {
    offsetDays: differenceInCalendarDays(barStart, rangeStart),
    spanDays: differenceInCalendarDays(barEnd, barStart) + 1,
  };
}

/** Groups consecutive days into month headers with their column spans. */
export function computeMonths(days: Date[]): { label: string; count: number }[] {
  const acc: { label: string; count: number }[] = [];
  for (const d of days) {
    const label = format(d, "yyyy年M月");
    const last = acc[acc.length - 1];
    if (last && last.label === label) last.count += 1;
    else acc.push({ label, count: 1 });
  }
  return acc;
}
