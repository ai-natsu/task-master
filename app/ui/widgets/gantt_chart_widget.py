"""ガントチャート（旧 client/src/components/GanttChart.tsx の移植）。

tkinter.Canvas に直接描画する。旧実装の「ラベル列を横スクロール時も固定表示」
という挙動は簡略化し、全体を1つのCanvasに描画して縦横スクロールする
（既知の簡略化）。
"""

import datetime
import tkinter as tk

import customtkinter as ctk

from app.db.holidays import list_holidays
from app.db.statuses import list_statuses
from app.db.tasks import list_tasks, reorder_tasks, update_task
from app.i18n import format_date, t
from app.logic.dnd import plan_row_drop
from app.logic.gantt import compute_bar, compute_months, compute_range
from app.logic.tree import build_task_tree, flatten_nodes
from app.ui import theme
from app.ui.widgets.task_edit import create_task_via_form, edit_task
from app.ui.widgets.tooltip import Tooltip

DAY_W = 28
ROW_H = 36
LABEL_W = 220
HEADER_H = 24
SUBHEADER_H = 20
_EDGE_PX = 6  # バー端のドラッグ判定幅(px)
_ROW_HOVER_BG = "#eef2ff"
_LABEL_HOVER_FG = "#4f46e5"
_DROP_EDGE = 0.25  # 行の上下この割合の範囲にドロップすると兄弟として挿入、中央なら子にする


def _lighten(color: str, ratio: float) -> str:
    """16進カラーを白に近づける（バーのマウスオーバー表示用）。"""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(*(round(c + (255 - c) * ratio) for c in (r, g, b)))


class GanttChartWidget(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, on_change=None, filters: dict | None = None):
        super().__init__(master, fg_color=theme.PANEL_BG)
        self.app = app
        self.project_id = project_id
        self.on_change = on_change or (lambda: None)
        self.filters = filters or {}
        self._range_start: datetime.date | None = None
        self._drag: dict | None = None
        self._rows_cache: list = []
        self._row_drag_id: str | None = None
        self._row_hl: dict[int, tuple[int, int, int, str]] = {}
        self._hover_row: int | None = None
        self._tip_key: tuple | None = None
        self._total_width = 0

        self.canvas = tk.Canvas(self, highlightthickness=0, background="#ffffff")
        h_scroll = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        v_scroll = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        self._tooltip = Tooltip(self.canvas)
        self.canvas.bind("<Motion>", self._on_canvas_motion, add="+")
        self.canvas.bind("<Leave>", self._on_canvas_leave)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.refresh()

    def set_filters(self, filters: dict) -> None:
        self.filters = filters
        self.refresh()

    def refresh(self) -> None:
        self._tooltip.hide()
        self.canvas.delete("all")
        self._row_hl = {}
        self._hover_row = None
        self._tip_key = None
        tasks = list_tasks(self.app.conn, project_id=self.project_id, **self.filters)
        statuses = {s.id: s for s in list_statuses(self.app.conn)}
        rows = flatten_nodes(build_task_tree(tasks))

        if not rows:
            self.canvas.create_text(
                20, 20, anchor="nw", text=t("タスクがありません。"), fill="#94a3b8",
                font=(theme.FONT_FAMILY, 11),
            )
            self.canvas.configure(scrollregion=(0, 0, 400, 60))
            return

        today = datetime.date.today()
        gantt_range = compute_range([flat.node.task for flat in rows], today)
        days = gantt_range.days
        months = compute_months(days)
        today_offset = (today - gantt_range.range_start).days
        self._range_start = gantt_range.range_start
        holiday_dates = {h.date for h in list_holidays(self.app.conn)}

        total_width = LABEL_W + len(days) * DAY_W
        self._total_width = total_width
        total_height = HEADER_H + SUBHEADER_H + len(rows) * ROW_H

        self._draw_month_header(months)
        self._draw_day_header(days, today, holiday_dates)
        self._draw_rows(
            rows, statuses, days, gantt_range.range_start, today_offset, total_width,
            holiday_dates,
        )
        self._draw_vertical_gridlines(days, total_height)
        # 次の行の土日祝シェーディングが罫線を覆い隠さないよう、罫線を前面に上げる。
        # バーはさらにその上(最前面)に来るようにする。
        self.canvas.tag_raise("rowline")
        self.canvas.tag_raise("bar")

        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

    def _draw_vertical_gridlines(self, days, total_height) -> None:
        grid_top = HEADER_H + SUBHEADER_H
        self.canvas.create_line(LABEL_W, 0, LABEL_W, total_height, fill="#e2e8f0")
        for i in range(len(days) + 1):
            x = LABEL_W + i * DAY_W
            self.canvas.create_line(x, grid_top, x, total_height, fill="#e2e8f0")

    def _draw_month_header(self, months) -> None:
        heading_font = (theme.FONT_FAMILY, 10, "bold")
        self.canvas.create_rectangle(0, 0, LABEL_W, HEADER_H, fill="#ffffff", outline="#e2e8f0")
        self.canvas.create_text(
            8, HEADER_H / 2, anchor="w", text=t("タスク"), fill="#64748b", font=heading_font
        )
        x = LABEL_W
        for month in months:
            w = month.count * DAY_W
            self.canvas.create_rectangle(x, 0, x + w, HEADER_H, outline="#e2e8f0")
            self.canvas.create_text(
                x + 4, HEADER_H / 2, anchor="w", text=month.label, fill="#64748b",
                font=heading_font,
            )
            x += w

    def _draw_day_header(self, days, today, holiday_dates: set[str]) -> None:
        y0 = HEADER_H
        self.canvas.create_rectangle(
            0, y0, LABEL_W, y0 + SUBHEADER_H, fill="#ffffff", outline="#e2e8f0"
        )
        for i, d in enumerate(days):
            dx = LABEL_W + i * DAY_W
            dow = d.weekday()
            bg, fg = None, "#94a3b8"
            if dow == 6 or d.isoformat() in holiday_dates:
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
                dx + DAY_W / 2, y0 + SUBHEADER_H / 2, text=str(d.day), fill=fg,
                font=(theme.FONT_FAMILY, 8),
            )

    def _draw_rows(
        self, rows, statuses, days, range_start, today_offset, total_width,
        holiday_dates: set[str],
    ) -> None:
        self._rows_cache = rows
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
            label_fg = "#94a3b8" if is_done else "#0f172a"
            label_text = self.canvas.create_text(
                dot_x + 12, row_y + ROW_H / 2, anchor="w", text=task.title,
                fill=label_fg, width=LABEL_W - dot_x - 16,
                font=(theme.FONT_FAMILY, 11),
            )

            for i, d in enumerate(days):
                dow = d.weekday()
                is_holiday = dow == 6 or d.isoformat() in holiday_dates
                if is_holiday or dow == 5:
                    dx = LABEL_W + i * DAY_W
                    self.canvas.create_rectangle(
                        dx, row_y, dx + DAY_W, row_y + ROW_H,
                        fill="#fef9f9" if is_holiday else "#f8fafc", outline="",
                    )
            row_hl = self.canvas.create_rectangle(
                LABEL_W, row_y, total_width, row_y + ROW_H, fill="", outline=""
            )
            self._row_hl[index] = (label_bg, row_hl, label_text, label_fg)
            self.canvas.create_line(
                0, row_y + ROW_H, total_width, row_y + ROW_H, fill="#e2e8f0", tags=("rowline",)
            )

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
                    stipple="gray50" if is_done else "", tags=("bar",),
                )
                self.canvas.tag_bind(
                    bar_item, "<ButtonPress-1>",
                    lambda e, tk_=task, bi=bar_item: self._on_bar_press(e, tk_, bi),
                )
                self.canvas.tag_bind(bar_item, "<B1-Motion>", self._on_bar_motion)
                self.canvas.tag_bind(bar_item, "<ButtonRelease-1>", self._on_bar_release)
                self.canvas.tag_bind(bar_item, "<Motion>", self._on_bar_hover)
                bar_color = status.color if status else "#6366f1"
                self.canvas.tag_bind(
                    bar_item, "<Enter>",
                    lambda e, bi=bar_item, c=bar_color, tk_=task: self._on_bar_enter(e, bi, c, tk_),
                )
                self.canvas.tag_bind(
                    bar_item, "<Double-Button-1>", lambda _e, tk_=task: self._edit(tk_)
                )
                self.canvas.tag_bind(
                    bar_item, "<Leave>",
                    lambda _e, bi=bar_item, c=bar_color: self._on_bar_leave(bi, c),
                )

            for label_item in (label_bg, label_text):
                self.canvas.tag_bind(
                    label_item, "<ButtonPress-1>",
                    lambda _e, tk_=task: self._on_row_press(tk_),
                )
                self.canvas.tag_bind(label_item, "<B1-Motion>", self._on_row_motion)
                self.canvas.tag_bind(label_item, "<ButtonRelease-1>", self._on_row_release)
                self.canvas.tag_bind(
                    label_item, "<Double-Button-1>", lambda _e, tk_=task: self._edit(tk_)
                )

    # --- 行ラベルのドラッグ（並べ替え・親の付け替え） -----------------------------
    def _row_drop_target(self, event) -> tuple[int, str] | None:
        """ポインタ位置から (行インデックス, ドロップ位置) を求める。範囲外は None。

        行の上端 25% = before（直前に兄弟として挿入）、下端 25% = after（直後）、
        中央 = child（その行の子にする）。
        """
        row_top = HEADER_H + SUBHEADER_H
        y = self.canvas.canvasy(event.y)
        index = int((y - row_top) // ROW_H)
        if not (0 <= index < len(self._rows_cache)):
            return None
        frac = ((y - row_top) % ROW_H) / ROW_H
        zone = "before" if frac < _DROP_EDGE else "after" if frac > 1 - _DROP_EDGE else "child"
        return index, zone

    def _draw_drop_indicator(self, index: int, zone: str) -> None:
        self.canvas.delete("drop_indicator")
        row_y = HEADER_H + SUBHEADER_H + index * ROW_H
        if zone == "child":
            self.canvas.create_rectangle(
                1, row_y + 1, self._total_width - 1, row_y + ROW_H - 1,
                outline=theme.ACCENT, width=2, tags=("drop_indicator",),
            )
        else:
            y = row_y if zone == "before" else row_y + ROW_H
            self.canvas.create_line(
                0, y, self._total_width, y, fill=theme.ACCENT, width=3, tags=("drop_indicator",)
            )

    def _on_row_press(self, task) -> None:
        self._row_drag_id = task.id
        self._tooltip.hide()

    def _on_row_motion(self, event) -> None:
        if not self._row_drag_id:
            return
        target = self._row_drop_target(event)
        if target is None:
            self.canvas.delete("drop_indicator")
            return
        self._draw_drop_indicator(*target)

    def _on_row_release(self, event) -> None:
        if not self._row_drag_id:
            return
        active_id, self._row_drag_id = self._row_drag_id, None
        self.canvas.delete("drop_indicator")
        target = self._row_drop_target(event)
        if target is None:
            return
        index, zone = target
        target_task = self._rows_cache[index].node.task
        if target_task.id == active_id:
            return

        tasks = list_tasks(self.app.conn, project_id=self.project_id)
        plan = plan_row_drop(tasks, active_id, target_task.id, zone)
        if plan.get("reorder"):
            reorder_tasks(self.app.conn, plan["reorder"])
            self.refresh()
            self.on_change()

    # --- マウスオーバー（行の強調・ツールチップ） -------------------------------
    def _is_dragging(self) -> bool:
        return self._drag is not None or self._row_drag_id is not None

    def _set_hover_row(self, index: int | None) -> None:
        if index == self._hover_row:
            return
        if self._hover_row in self._row_hl:
            label_bg, row_hl, label_text, label_fg = self._row_hl[self._hover_row]
            self.canvas.itemconfigure(label_bg, fill="#ffffff")
            self.canvas.itemconfigure(row_hl, fill="")
            self.canvas.itemconfigure(label_text, fill=label_fg)
        self._hover_row = index
        if index in self._row_hl:
            label_bg, row_hl, label_text, _fg = self._row_hl[index]
            self.canvas.itemconfigure(label_bg, fill=_ROW_HOVER_BG)
            self.canvas.itemconfigure(row_hl, fill=_ROW_HOVER_BG)
            self.canvas.itemconfigure(label_text, fill=_LABEL_HOVER_FG)

    def _on_canvas_motion(self, event) -> None:
        if self._is_dragging():
            return
        row_top = HEADER_H + SUBHEADER_H
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        index = int((y - row_top) // ROW_H) if y >= row_top else -1
        index = index if 0 <= index < len(self._rows_cache) else None
        self._set_hover_row(index)

        key = ("label", index) if index is not None and x < LABEL_W else None
        if key != self._tip_key:
            self._tip_key = key
            self._tooltip.hide()
            if key is not None:
                task = self._rows_cache[index].node.task
                text = f"{task.title}\n{t('ダブルクリックで編集')}"
                self._tooltip.schedule(text, event.x_root, event.y_root)

    def _on_canvas_leave(self, _event) -> None:
        self._set_hover_row(None)
        self._tip_key = None
        self._tooltip.hide()
        self.canvas.configure(cursor="")

    def _on_bar_enter(self, event, bar_item: int, color: str, task) -> None:
        if self._is_dragging():
            return
        self.canvas.itemconfigure(bar_item, fill=_lighten(color, 0.3))
        start = format_date(task.start_date) or "?"
        due = format_date(task.due_date) or "?"
        self._tooltip.schedule(f"{task.title}\n{start} 〜 {due}", event.x_root, event.y_root)

    def _on_bar_leave(self, bar_item: int, color: str) -> None:
        self.canvas.configure(cursor="")
        self._tooltip.hide()
        if self._drag is None:
            self.canvas.itemconfigure(bar_item, fill=color)

    # --- ガントバーのドラッグ（平行移動・端のリサイズ） -------------------
    def _bar_mode_at(self, event_x: float, x0: float, x1: float) -> str:
        if event_x - x0 <= _EDGE_PX:
            return "resize-left"
        if x1 - event_x <= _EDGE_PX:
            return "resize-right"
        return "move"

    def _on_bar_hover(self, event) -> None:
        item = self.canvas.find_withtag("current")
        if not item:
            return
        x0, _y0, x1, _y1 = self.canvas.coords(item[0])
        mode = self._bar_mode_at(event.x, x0, x1)
        cursor = "sb_h_double_arrow" if mode != "move" else "fleur"
        self.canvas.configure(cursor=cursor)

    def _on_bar_press(self, event, task, bar_item: int) -> None:
        self._tooltip.hide()
        coords = self.canvas.coords(bar_item)
        x0, _y0, x1, _y1 = coords
        mode = self._bar_mode_at(event.x, x0, x1)
        self._drag = {
            "task": task, "bar_item": bar_item, "mode": mode,
            "start_x": event.x, "orig_coords": coords, "moved": False,
        }

    def _on_bar_motion(self, event) -> None:
        drag = self._drag
        if drag is None:
            return
        dx = event.x - drag["start_x"]
        if abs(dx) > 2:
            drag["moved"] = True
        x0, y0, x1, y1 = drag["orig_coords"]
        if drag["mode"] == "move":
            new_x0, new_x1 = x0 + dx, x1 + dx
        elif drag["mode"] == "resize-left":
            new_x0, new_x1 = min(x0 + dx, x1 - DAY_W), x1
        else:  # resize-right
            new_x0, new_x1 = x0, max(x1 + dx, x0 + DAY_W)
        self.canvas.coords(drag["bar_item"], new_x0, y0, new_x1, y1)
        drag["live_coords"] = (new_x0, y0, new_x1, y1)

    def _on_bar_release(self, _event) -> None:
        drag, self._drag = self._drag, None
        if drag is None:
            return
        task = drag["task"]
        if not drag["moved"]:
            return  # シングルクリックでは何もしない（編集はダブルクリック）

        x0, _y0, x1, _y1 = drag.get("live_coords", drag["orig_coords"])
        range_start = self._range_start
        start_offset = round((x0 - 2 - LABEL_W) / DAY_W)
        due_offset = round((x1 + 2 - LABEL_W) / DAY_W) - 1
        new_start = range_start + datetime.timedelta(days=start_offset)
        new_due = range_start + datetime.timedelta(days=max(due_offset, start_offset))

        update_task(
            self.app.conn, task.id,
            start_date=new_start.isoformat(), due_date=new_due.isoformat(),
        )
        self.refresh()
        self.on_change()

    def _edit(self, task) -> None:
        if edit_task(self.app, self.project_id, task):
            self.refresh()
            self.on_change()

    def add_root_task(self) -> None:
        if create_task_via_form(self.app, self.project_id):
            self.refresh()
            self.on_change()
