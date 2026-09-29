# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TaskMaster — a single-process desktop task manager (Python + CustomTkinter) with projects (archivable), unlimited-depth subtasks, tags, priorities, start/due dates, drag-and-drop reordering, tree/kanban/Gantt views, and a stats dashboard. All UI text is in Japanese. Distributed as a single `TaskMaster.exe` (built with Nuitka) so end users need neither Python nor Node.js installed.

This was a full rewrite (2026) of an earlier Express+Prisma+React web app to this Python desktop app, driven by the need for a Node.js-free, single-executable distribution with harder-to-read source than plain JS. `git log` before the rewrite commit has the old implementation if a past behavior needs to be checked.

## Commands

Run from the repo root.

- `pip install -e .[dev]` — install the app and dev dependencies (customtkinter, pytest, ruff, mypy, nuitka)
- `python -m app.main` — run the desktop app (creates/opens `taskmaster.db` in the repo root during dev; see Packaging below for where it lives once built)
- `python seed.py` — **destructive**: wipes all data and repopulates with sample projects/tasks/tags (mirrors the old `prisma/seed.ts` fixture)

Testing (pytest for both pure-function unit tests and SQLite integration tests — no GUI automation, see below):

- `python -m pytest` — runs `tests/unit` (tree/dnd/gantt pure functions) and `tests/integration` (data layer against a temp SQLite file per test, via the `conn`/`statuses` fixtures in `tests/conftest.py`)
- No test touches the dev `taskmaster.db`; each integration test gets its own file in a temp dir
- GUI screens (`app/ui/*`) have no automated test coverage — Tkinter has no mature Playwright-equivalent. Verify GUI changes manually by running `python -m app.main`, or with a short-lived smoke script that constructs the widget, calls `.update()`, and destroys it (see recent commits for the pattern used during development)

Static analysis (ruff only; config in `pyproject.toml`). mypy is available as a dev dependency but is **not** an enforced gate (same "one enforced tool, formatting/typing deferred" philosophy as the old ESLint-only setup) — expect some pre-existing mypy noise from dynamic patterns (sentinel objects for "unset" kwargs, Tkinter's loosely-typed widget tree).

- `python -m ruff check .` / `python -m ruff check --fix .`

## Packaging (Nuitka)

- `python packaging/build_exe.py` — builds `packaging/dist/TaskMaster.exe` (gitignored). Takes several minutes; downloads the `zig` C-compiler backend on first run (`--zig --assume-yes-for-downloads`, needed because Nuitka's MinGW64 auto-download only supports Python ≤3.12)
- The exe embeds the Python interpreter, CustomTkinter/Tk assets, and `app/db/schema.sql` (via `--include-data-files`, since it's not a `.py` file Nuitka would otherwise pick up)
- **Not** embedded: `taskmaster.db` — created next to the exe on first run (user requirement: DB file stays a separate, inspectable file alongside the binary, not baked in)
- Path resolution for "next to the exe" (`app/db/connection.py:get_app_dir`) is the trickiest part of packaging: Nuitka's `NUITKA_ONEFILE_PARENT` env var is **not** the exe's path — it's the PID of the onefile bootstrap process (confirmed by reading Nuitka's generated `OnefileBootstrap.c`). The correct exe path is resolved from that PID via `ctypes` + `QueryFullProcessImageNameW` (Windows-only, matching the packaging target). Don't "fix" this back to treating the env var as a path — it was tried and fails with `sqlite3.OperationalError: unable to open database file`.
- First launch also needs statuses to exist before any task can be created; `app/main.py` calls `ensure_default_statuses()` (non-destructive: inserts the 4 default statuses only if the table is empty). This is deliberately *not* baked into `connect()`/`_ensure_schema()` in `connection.py`, so tests and `seed.py` keep seeing a schema-only DB.

## Architecture

Single process, no HTTP layer — the UI calls the data/logic layers directly as Python function calls.

**app/db/** — SQLite access via the stdlib `sqlite3` module directly (no ORM). `schema.sql` is the DDL (ported from the old `prisma/schema.prisma`; same models/cascades: `Project 1—N Task`, self-referential `Task.parentId` with `ON DELETE CASCADE`, `Task N—N Tag` via `TaskTag`, `Task.status` FK to `Status` with `ON DELETE RESTRICT`).

- `connection.py` — `connect()` resolves the DB path (see Packaging above), applies `schema.sql` once via `PRAGMA user_version`, and enables `PRAGMA foreign_keys`
- `projects.py` / `tasks.py` / `tags.py` / `statuses.py` / `stats.py` — one module per resource, each a direct port of the equivalent `server/src/routes/*.ts` business logic (reorder-via-transaction, cycle detection, archive filtering, `isDone`-driven stats — see below)
- `errors.py` — `NotFoundError` / `ValidationError` / `ConflictError` / `CycleError`, raised by the db layer and caught by the UI layer to show dialogs
- `tasks.py:is_descendant_or_self` + `move_task` reject moving a task under itself or its own subtree; **only `move_task` can change `parent_id`** — `update_task` deliberately has no `parent_id` parameter, so every parent change goes through cycle detection (the old TS app's `TaskFormModal` edit path bypassed this by calling plain `update`, not `move`; this rewrite closes that gap rather than reproducing it)
- `Project.archived`: archived projects are excluded from `list_projects()` (unless `include_archived=True`) and from `list_tasks()`/`get_stats()` when no explicit `project_id` is given
- `stats.py`: "done" is always derived from `Status.is_done`, never a hardcoded status id — same rule the old app followed

**app/logic/** — pure functions ported from `client/src/utils/*.ts`, unit-tested in isolation:

- `tree.py` — `build_task_tree`/`flatten_nodes`/`flatten_with_depth`; a task whose `parent_id` isn't present in the given list becomes a root (used by search/filter results)
- `dnd.py` — `plan_kanban_drag`/`plan_tree_drag`; pure decision functions that take the current tasks + drag target and return `{"reorder": [...], "status_change": {...}}` for the UI to apply. `_array_move` replicates `@dnd-kit/sortable`'s `arrayMove` index semantics exactly (see the function's docstring before changing it)
- `gantt.py` — `compute_range`/`compute_bar`/`compute_months`; range always includes "today", padded -3/+7 days

**app/ui/** — CustomTkinter. `app_window.py` is the root window (sidebar + a single content frame that `navigate(route, **kwargs)` swaps views into, replacing react-router). `sidebar.py`, `dashboard_view.py`, `projects_list_view.py`, `settings_view.py`, `project_view.py` are one module per screen. `project_view.py` hosts a `CTkSegmentedButton` to switch the three `widgets/*_widget.py` views (tree/kanban/gantt) in place.

- `widgets/task_tree_widget.py` — `ttk.Treeview` (not pure CustomTkinter — it's the only widget with native expand/collapse); drag-and-drop is `ButtonPress`/`ButtonRelease` position tracking feeding `plan_tree_drag`, not a native DnD API
- `widgets/kanban_board_widget.py` — cards are plain `CTkFrame`s; drag-and-drop uses `winfo_containing(event.x_root, event.y_root)` at release time to find whatever's under the cursor, then walks `.master` up to find the owning card/column. No floating drag-preview (known simplification vs. the old `DragOverlay`)
- `widgets/gantt_chart_widget.py` — `tkinter.Canvas`, drawn from scratch each `refresh()`. The old web version kept the row-label column sticky during horizontal scroll; this port scrolls everything together (known simplification)
- `widgets/task_form_dialog.py` / `project_form_dialog.py` / `confirm_dialog.py` — modal `CTkToplevel`s that block via `parent.wait_window(dialog)` and expose an `ask_*(...)` module function returning `None` on cancel

## Known gaps carried over from the old app (not fixed in the rewrite; rewrite scope only)

- No tag management screen (tags are create-only, from the task form)
- No error message shown on save failure in the task form
- These match the pre-rewrite app's documented gaps — see `git log` on the pre-rewrite commit for `docs/` if more detail is needed before it was removed
