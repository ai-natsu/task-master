# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TaskMaster — a full-stack task management app with projects (archivable), unlimited-depth subtasks, tags, priorities, start/due dates, search/filter, drag-and-drop reordering, tree/kanban/Gantt views, and a stats dashboard. All UI text is in Japanese.

## Commands

Run from the repo root (npm workspaces: `server`, `client`).

- `npm install` — install all workspace dependencies
- `npm run dev:server` — start the API on http://localhost:3001 (tsx watch)
- `npm run dev:client` — start the Vite dev server on http://localhost:5173 (proxies `/api` to 3001)
- `npm run build` — build both workspaces

Server-only (run from `server/`):
- `npx prisma migrate dev --name <name>` — create/apply a migration after editing `prisma/schema.prisma`
- `npx prisma generate` — regenerate the Prisma client
- `npm run seed` — reset and repopulate `dev.db` with sample projects/tasks/tags (destructive: deletes all rows first)

Testing (Vitest for unit/integration, Playwright for E2E — separate scripts; see `docs/TEST_DESIGN.md`):
- `npm test` — Vitest across both workspaces (`server` API integration via Supertest on `server/test.db`; `client` unit/component on jsdom)
- `npm run test:e2e` — Playwright E2E; `playwright.config.ts` `webServer` auto-starts server+client on a dedicated `server/e2e.db` (first run: `npx playwright install chromium`)
- Server tests reset `test.db` in `src/test/setup.ts`; `createApp()` in `src/app.ts` is exported separately from `src/index.ts` so Supertest can mount it without `listen`. Kanban/tree drag decisions live in `client/src/utils/dnd.ts` as pure functions (`planKanbanDrag`/`planTreeDrag`) for unit testing. No test touches `dev.db`.

Windows note: Node.js was installed via winget; if a shell doesn't see `node`/`npm` on PATH, prepend the current session PATH from machine+user env vars, or use the full path `C:\Program Files\nodejs\`. `.claude/launch.json` uses `server/dev.cmd` and `client/dev.cmd` wrapper scripts (not raw `npm`) so the preview tool's dev servers can find Node regardless of its own stale PATH.

## Architecture

**server/** — Express + TypeScript + Prisma + SQLite (`server/dev.db`, schema in `server/prisma/schema.prisma`).
- `src/index.ts` — Express app wiring; routes mounted under `/api/{projects,tasks,tags,stats}`
- `src/routes/*.ts` — one router per resource; validation via `zod` schemas defined inline in each file
- `src/db.ts` — shared `PrismaClient` singleton
- Data model: `Project 1—N Task`, `Task` is self-referential (`parentId` → unlimited subtask nesting, `onDelete: Cascade`), `Task N—N Tag` via the `TaskTag` join model. `Task.status` is a FK to the user-editable `Status` table (`onDelete: Restrict`; rows have `label`/`color`/`order`/`isDone`, managed via `/api/statuses` and the client's `/settings` page; the migration seeds `TODO`/`IN_PROGRESS`/`DONE`, whose ids are those literal strings — new ones get cuids). `isDone` drives completion-rate/overdue semantics in stats and the UI (never hardcode `"DONE"` checks). `priority` is a plain `String` column (not a Prisma enum — SQLite's connector doesn't support them); allowed values live in `src/constants.ts` and are enforced by zod at the API boundary.
- `Project.archived`: archived projects are excluded from `GET /api/projects` (unless `?includeArchived=true`), from `GET /api/tasks` without a `projectId`, and from global stats. Archive/restore is just `PATCH /api/projects/:id {archived}` from the client's `/projects` list page.
- Reordering: every `Project`/`Task` row has an `order` int. `PATCH /api/tasks/reorder` and `/api/projects/reorder` take an explicit `{id, order}[]` (or `{ids}`) list and apply it in one `$transaction`.
- Moving a task between parents (`PATCH /api/tasks/:id/move`) walks descendants (`isDescendantOrSelf` in `routes/tasks.ts`) to reject cycles before writing.

**client/** — React + TypeScript + Vite + Tailwind, React Query for all server state, `react-router-dom` for routing, `@dnd-kit` for drag-and-drop.
- `src/api/*.ts` — one file per resource, each exporting React Query hooks (`useTasks`, `useCreateTask`, etc.); `src/api/client.ts` is the thin `fetch` wrapper all of them share
- `src/utils/tree.ts` — converts the flat `Task[]` the API returns into a nested tree (`buildTaskTree`) and back to a flat, depth-annotated list for the "parent task" picker (`flattenWithDepth`); the tree is rebuilt client-side, the server only ever stores/returns flat rows with `parentId`
- `src/components/TaskTree.tsx` + `TaskNode.tsx` — recursive tree renderer; a single top-level `DndContext` wraps nested per-level `SortableContext`s (one per sibling group) so drag-and-drop reordering works at any depth. `onDragEnd` only reorders within the same `parentId` group — moving a task to a *different* parent is done via the parent-picker in the edit form, not by dragging.
- `src/components/GanttChart.tsx` — day-grid Gantt (bars span `startDate`→`dueDate`, single-day bar if only one is set); third view mode in `ProjectView` alongside tree and kanban
- `src/pages/ProjectView.tsx` — when no filters (search/status/priority/tag) are active it renders the unfiltered task list (needed so the tree stays intact); as soon as a filter is active it switches to the server-filtered flat list instead, since filtering by matching descendants only doesn't make sense as a tree
- `src/pages/Dashboard.tsx` — cross-project overview (global stats, overdue/upcoming lists, project cards)

Ports: server 3001, client 5173 (Vite proxies `/api/*` to the server — see `client/vite.config.ts`).
