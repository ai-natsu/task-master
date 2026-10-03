import { z } from "zod";
import { PRIORITIES } from "./constants.js";

// Request-body schemas for every route, kept here rather than inline so they
// can be unit-tested directly (schemas.test.ts) instead of only through HTTP.

export const projectCreateSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000).optional(),
  color: z.string().optional(),
});

export const projectUpdateSchema = projectCreateSchema.partial().extend({
  archived: z.boolean().optional(),
});

export const projectReorderSchema = z.object({
  ids: z.array(z.string()),
});

export const taskCreateSchema = z.object({
  title: z.string().min(1).max(300),
  description: z.string().max(5000).optional(),
  projectId: z.string(),
  parentId: z.string().nullable().optional(),
  status: z.string().optional(),
  priority: z.enum(PRIORITIES).optional(),
  startDate: z.string().datetime().nullable().optional(),
  dueDate: z.string().datetime().nullable().optional(),
  tagIds: z.array(z.string()).optional(),
});

export const taskUpdateSchema = z.object({
  title: z.string().min(1).max(300).optional(),
  description: z.string().max(5000).nullable().optional(),
  status: z.string().optional(),
  priority: z.enum(PRIORITIES).optional(),
  startDate: z.string().datetime().nullable().optional(),
  dueDate: z.string().datetime().nullable().optional(),
  tagIds: z.array(z.string()).optional(),
});

export const taskMoveSchema = z.object({
  parentId: z.string().nullable().optional(),
  projectId: z.string().optional(),
  order: z.number().int().optional(),
});

export const taskReorderSchema = z.object({
  items: z.array(
    z.object({
      id: z.string(),
      order: z.number().int(),
      parentId: z.string().nullable().optional(),
      projectId: z.string().optional(),
    })
  ),
});

export const tagCreateSchema = z.object({
  name: z.string().min(1).max(50),
  color: z.string().optional(),
});

export const statusCreateSchema = z.object({
  label: z.string().min(1).max(50),
  color: z.string().optional(),
  isDone: z.boolean().optional(),
});

export const statusUpdateSchema = z.object({
  label: z.string().min(1).max(50).optional(),
  color: z.string().optional(),
  isDone: z.boolean().optional(),
});

export const statusReorderSchema = z.object({
  ids: z.array(z.string()),
});

// 祝日の日付は "YYYY-MM-DD"。存在しない日付（2026-02-30 など）は拒否する。
const holidayDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/)
  .refine((d) => {
    const time = Date.parse(`${d}T00:00:00Z`);
    return !Number.isNaN(time) && new Date(time).toISOString().slice(0, 10) === d;
  }, "invalid date");

export const holidayUpsertSchema = z.object({
  date: holidayDate,
  name: z.string().trim().min(1).max(100),
});

export const holidayUpdateSchema = z.object({
  name: z.string().trim().min(1).max(100),
});

export const holidayBulkSchema = z.object({
  rows: z.array(holidayUpsertSchema).max(2000),
});
