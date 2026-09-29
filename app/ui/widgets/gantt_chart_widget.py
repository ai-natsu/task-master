"""ガントチャート（旧 client/src/components/GanttChart.tsx の移植）。

tkinter.Canvas に直接描画する。旧実装の「ラベル列を横スクロール時も固定表示」
という挙動は簡略化し、全体を1つのCanvasに描画して縦横スクロールする
（既知の簡略化）。
"""

import datetime
import tkinter as tk

import customtkinter as ctk

from app.db.statuses import list_statuses
from app.db.tasks import create_task, list_tasks, update_task
from app.logic.gantt import compute_bar, compute_months, compute_range
from app.logic.tree import build_task_tree, flatten_nodes
from app.ui.widgets.task_form_dialog import ask_task_form

DAY_W = 28
ROW_H = 36
LABEL_W = 220
HEADER_H = 24
SUBHEADER_H = 20


class GanttChartWidget(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self.on_change = on_change or (lambda: None)

        self.canvas = tk.Canvas(self, highlightthickness=0, background="#ffffff")
        h_scroll = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        v_scroll = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.refresh()

    def refresh(self) -> None:
        self.canvas.delete("all")
        tasks = list_tasks(self.app.conn, project_id=self.project_id)
        statuses = {s.id: s for s in list_statuses(self.app.conn)}
        rows = flatten_nodes(build_task_tree(tasks))

        if not rows:
            self.canvas.create_text(
                20, 20, anchor="nw", text="タスクがありません。", fill="#94a3b8"
            )
            self.canvas.configure(scrollregion=(0, 0, 400, 60))
            return

        today = datetime.date.today()
        gantt_range = compute_range([flat.node.task for flat in rows], today)
        days = gantt_range.days
        months = compute_months(days)
        today_offset = (today - gantt_range.range_start).days

        total_width = LABEL_W + len(days) * DAY_W
        total_height = HEADER_H + SUBHEADER_H + len(rows) * ROW_H

        self._draw_month_header(months)
        self._draw_day_header(days, today)
        self._draw_rows(rows, statuses, days, gantt_range.range_start, today_offset, total_width)

        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

    def _draw_month_header(self, months) -> None:
        self.canvas.create_rectangle(0, 0, LABEL_W, HEADER_H, fill="#ffffff", outline="#e2e8f0")
        self.canvas.create_text(8, HEADER_H / 2, anchor="w", text="タスク", fill="#64748b")
        x = LABEL_W
        for month in months:
            w = month.count * DAY_W
            self.canvas.create_rectangle(x, 0, x + w, HEADER_H, outline="#e2e8f0")
            self.canvas.create_text(
                x + 4, HEADER_H / 2, anchor="w", text=month.label, fill="#64748b"
            )
            x += w

    def _draw_day_header(self, days, today) -> None:
        y0 = HEADER_H
        self.canvas.create_rectangle(
            0, y0, LABEL_W, y0 + SUBHEADER_H, fill="#ffffff", outline="#e2e8f0"
        )
        for i, d in enumerate(days):
            dx = LABEL_W + i * DAY_W
            dow = d.weekday()
            bg, fg = None, "#94a3b8"
            if dow == 6:
                bg, fg = "#fef2f2", "#f87171"
            elif dow == 5:
                bg, fg = "#eff6ff", "#60a5fa"
            if d == today:
                bg, fg = "#fef3c7", "#b45309"
            if bg:
                self.canvas.create_rectangle(
                    dx, y0, dx + DAY_W, y0 + SUBHEADER_H, fill=bg, outline=""
                )
            self.canvas.create_text(
                dx + DAY_W / 2, y0 + SUBHEADER_H / 2, text=str(d.day), fill=fg, font=("", 8)
            )

    def _draw_rows(self, rows, statuses, days, range_start, today_offset, total_width) -> None:
        row_top = HEADER_H + SUBHEADER_H
        for index, flat in enumerate(rows):
            task = flat.node.task
            status = statuses.get(task.status)
            is_done = status.is_done if status else False
            row_y = row_top + index * ROW_H

            label_bg = self.canvas.create_rectangle(
                0, row_y, LABEL_W, row_y + ROW_H, fill="#ffffff", outline="#f1f5f9"
            )
            dot_x = 12 + flat.depth * 16
            dot_color = status.color if status else "#94a3b8"
            self.canvas.create_oval(
                dot_x, row_y + ROW_H / 2 - 3, dot_x + 6, row_y + ROW_H / 2 + 3,
                fill=dot_color, outline="",
            )
            label_text = self.canvas.create_text(
                dot_x + 12, row_y + ROW_H / 2, anchor="w", text=task.title,
                fill="#94a3b8" if is_done else "#0f172a", width=LABEL_W - dot_x - 16,
            )

            for i, d in enumerate(days):
                dow = d.weekday()
                if dow in (5, 6):
                    dx = LABEL_W + i * DAY_W
                    self.canvas.create_rectangle(
                        dx, row_y, dx + DAY_W, row_y + ROW_H,
                        fill="#f8fafc" if dow == 5 else "#fef9f9", outline="",
                    )
            self.canvas.create_line(0, row_y + ROW_H, total_width, row_y + ROW_H, fill="#f1f5f9")

            if 0 <= today_offset < len(days):
                tx = LABEL_W + today_offset * DAY_W + DAY_W / 2
                self.canvas.create_line(tx, row_y, tx, row_y + ROW_H, fill="#fbbf24")

            bar = compute_bar(task, range_start)
            if bar:
                bx = LABEL_W + bar.offset_days * DAY_W + 2
                bw = max(bar.span_days * DAY_W - 4, DAY_W - 4)
                bar_item = self.canvas.create_rectangle(
                    bx, row_y + ROW_H / 2 - 8, bx + bw, row_y + ROW_H / 2 + 8,
                    fill=status.color if status else "#6366f1", outline="",
                    stipple="gray50" if is_done else "",
                )
                self.canvas.tag_bind(bar_item, "<Button-1>", lambda _e, t=task: self._edit(t))

            self.canvas.tag_bind(label_bg, "<Button-1>", lambda _e, t=task: self._edit(t))
            self.canvas.tag_bind(label_text, "<Button-1>", lambda _e, t=task: self._edit(t))

    def _edit(self, task) -> None:
        result = ask_task_form(self.app, self.app.conn, self.project_id, task=task)
        if result:
            result.pop("parent_id", None)
            update_task(self.app.conn, task.id, **result)
            self.refresh()
            self.on_change()

    def add_root_task(self) -> None:
        result = ask_task_form(self.app, self.app.conn, self.project_id)
        if result:
            result.pop("parent_id", None)
            create_task(self.app.conn, project_id=self.project_id, **result)
            self.refresh()
            self.on_change()
