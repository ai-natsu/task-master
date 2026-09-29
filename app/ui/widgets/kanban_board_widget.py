"""カンバンボード（旧 client/src/components/KanbanBoard.tsx の移植）。

CustomTkinter/Tkinter にはドラッグ用のネイティブAPIが無いため、
ButtonPress-1でドラッグ開始位置を記録し、ButtonRelease-1で
winfo_containing()により実際にカーソル下にあるウィジェットを特定して
列/カードを判定する方式を採る（フローティングのドラッグ中プレビューは省略）。
"""

import datetime

import customtkinter as ctk

from app.db.statuses import list_statuses
from app.db.tasks import create_task, list_tasks, reorder_tasks, update_task
from app.logic.dnd import plan_kanban_drag
from app.ui import theme
from app.ui.widgets.badges import color_pill, priority_badge
from app.ui.widgets.task_form_dialog import ask_task_form


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class KanbanBoardWidget(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, on_change=None, filters: dict | None = None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self.on_change = on_change or (lambda: None)
        self.filters = filters or {}

        self._drag_task_id: str | None = None
        self._card_widgets: dict[str, ctk.CTkFrame] = {}
        self._column_containers: dict[int, str] = {}

        self.scroll = ctk.CTkScrollableFrame(
            self, orientation="horizontal", fg_color="transparent"
        )
        self.scroll.pack(fill="both", expand=True)

        self.refresh()

    def set_filters(self, filters: dict) -> None:
        self.filters = filters
        self.refresh()

    def refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self._card_widgets.clear()
        self._column_containers.clear()

        statuses = list_statuses(self.app.conn)
        tasks = list_tasks(self.app.conn, project_id=self.project_id, **self.filters)
        columns: dict[str, list] = {s.id: [] for s in statuses}
        for t in tasks:
            columns.setdefault(t.status, []).append(t)
        for col in columns.values():
            col.sort(key=lambda t: t.order)

        for status in statuses:
            col_frame = ctk.CTkFrame(
                self.scroll, width=272, fg_color=theme.SUBTLE_BG, corner_radius=14
            )
            col_frame.pack(side="left", fill="y", padx=6, pady=4)
            col_frame.pack_propagate(False)
            self._column_containers[id(col_frame)] = status.id

            header = ctk.CTkFrame(col_frame, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(12, 6))
            ctk.CTkLabel(
                header, text="●", text_color=status.color, width=14, font=ctk.CTkFont(size=14)
            ).pack(side="left")
            ctk.CTkLabel(
                header, text=status.label, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")
            ctk.CTkLabel(
                header,
                text=str(len(columns.get(status.id, []))),
                fg_color=("#e2e8f0", "#334155"),
                text_color=theme.TEXT_PRIMARY,
                corner_radius=8,
                width=22,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right")

            cards_area = ctk.CTkFrame(col_frame, fg_color="transparent")
            cards_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self._column_containers[id(cards_area)] = status.id

            col_tasks = columns.get(status.id, [])
            if not col_tasks:
                ctk.CTkLabel(cards_area, text="ここにドロップ", text_color=theme.TEXT_MUTED).pack(
                    pady=20
                )
            for task in col_tasks:
                self._build_card(cards_area, task, status.is_done)

    def _build_card(self, parent, task, is_done: bool) -> None:
        card = ctk.CTkFrame(
            parent, corner_radius=10, border_width=1,
            fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER,
        )
        card.pack(fill="x", pady=4)
        self._card_widgets[task.id] = card

        title_label = ctk.CTkLabel(
            card,
            text=task.title,
            anchor="w",
            font=ctk.CTkFont(overstrike=is_done, weight="bold"),
            text_color=theme.TEXT_MUTED if is_done else theme.TEXT_PRIMARY,
            justify="left",
        )
        title_label.pack(fill="x", padx=10, pady=(10, 4))

        meta_row = ctk.CTkFrame(card, fg_color="transparent")
        meta_row.pack(fill="x", padx=10, pady=(0, 10))
        priority_badge(meta_row, task.priority).pack(side="left")
        for tag in task.tags:
            color_pill(meta_row, tag.name, tag.color).pack(side="left", padx=(4, 0))
        if task.due_date:
            overdue = not is_done and task.due_date < _now_iso()
            ctk.CTkLabel(
                meta_row,
                text=task.due_date[:10],
                text_color="#dc2626" if overdue else theme.TEXT_MUTED,
            ).pack(side="right")

        for widget in (card, title_label, meta_row):
            widget.bind("<ButtonPress-1>", lambda _e, t=task: self._start_drag(t))
            widget.bind("<ButtonRelease-1>", self._end_drag)
            widget.bind("<Double-Button-1>", lambda _e, t=task: self._edit(t))

    def _start_drag(self, task) -> None:
        self._drag_task_id = task.id
        card = self._card_widgets.get(task.id)
        if card:
            card.configure(border_color="#6366f1", border_width=2)

    def _end_drag(self, event) -> None:
        if not self._drag_task_id:
            return
        active_id, self._drag_task_id = self._drag_task_id, None
        card = self._card_widgets.get(active_id)
        if card:
            card.configure(border_width=1)

        target_widget = self.winfo_containing(event.x_root, event.y_root)
        over = self._resolve_drop_target(target_widget)
        if over is None:
            return

        tasks = list_tasks(self.app.conn, project_id=self.project_id)
        plan = plan_kanban_drag(tasks, active_id, over)
        if plan.get("status_change"):
            update_task(
                self.app.conn,
                plan["status_change"]["id"],
                status=plan["status_change"]["status"],
            )
        if plan.get("reorder"):
            reorder_tasks(self.app.conn, plan["reorder"])
        if plan:
            self.refresh()
            self.on_change()

    def _resolve_drop_target(self, widget) -> dict | None:
        w = widget
        while w is not None:
            for task_id, card in self._card_widgets.items():
                if w is card:
                    return {"id": task_id, "type": "card"}
            status_id = self._column_containers.get(id(w))
            if status_id is not None:
                return {"id": f"column:{status_id}", "type": "column", "status_id": status_id}
            w = getattr(w, "master", None)
        return None

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
