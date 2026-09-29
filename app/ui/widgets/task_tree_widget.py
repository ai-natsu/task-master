"""タスクツリー表示（旧 client/src/components/TaskTree.tsx + TaskNode.tsx の移植）。

ttk.Treeview はネイティブに展開/折りたたみを持つため採用し、ドラッグ&ドロップは
マウスイベントで検出して純粋関数 plan_tree_drag に委ねる（同じ親配下のみ並べ替え、
という元実装の制約はそのまま）。
"""

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from app.db.errors import CycleError
from app.db.statuses import list_statuses
from app.db.tasks import create_task, delete_task, list_tasks, move_task, reorder_tasks, update_task
from app.logic.dnd import plan_tree_drag
from app.logic.tree import build_task_tree, flatten_nodes
from app.ui import theme
from app.ui.widgets.confirm_dialog import ask_confirm
from app.ui.widgets.task_form_dialog import PRIORITY_LABELS, ask_task_form

_EMPTY_IID = "__empty__"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class TaskTreeWidget(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, on_change=None, filters: dict | None = None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self.on_change = on_change or (lambda: None)
        self.filters = filters or {}
        self._tasks_by_id: dict = {}
        self._status_labels: dict[str, str] = {}
        self._drag_id: str | None = None

        style = ttk.Style()
        style.configure(
            "TaskTree.Treeview",
            rowheight=34,
            background=theme.CARD_BG[0],
            fieldbackground=theme.CARD_BG[0],
            foreground=theme.TEXT_PRIMARY[0],
            borderwidth=0,
            font=(theme.FONT_FAMILY, 11),
        )
        style.configure(
            "TaskTree.Treeview.Heading",
            background=("#f1f5f9"),
            foreground=theme.TEXT_MUTED[0],
            relief="flat",
            font=(theme.FONT_FAMILY, 10, "bold"),
        )
        style.map(
            "TaskTree.Treeview",
            background=[("selected", theme.ACCENT)],
            foreground=[("selected", "#ffffff")],
        )

        self.tree = ttk.Treeview(
            self,
            style="TaskTree.Treeview",
            columns=("status", "priority", "tags", "due"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="タスク")
        self.tree.heading("status", text="ステータス")
        self.tree.heading("priority", text="優先度")
        self.tree.heading("tags", text="タグ")
        self.tree.heading("due", text="期限")
        self.tree.column("#0", width=320, stretch=True)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("priority", width=70, anchor="center")
        self.tree.column("tags", width=160)
        self.tree.column("due", width=90, anchor="center")

        self.tree.tag_configure("overdue", foreground="#dc2626")
        self.tree.tag_configure("done", foreground="#94a3b8")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonPress-1>", self._on_press)
        self.tree.bind("<ButtonRelease-1>", self._on_release)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)

        self.refresh()

    def set_filters(self, filters: dict) -> None:
        self.filters = filters
        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())

        tasks = list_tasks(self.app.conn, project_id=self.project_id, **self.filters)
        self._tasks_by_id = {t.id: t for t in tasks}
        statuses = {s.id: s for s in list_statuses(self.app.conn)}
        self._status_labels = {sid: s.label for sid, s in statuses.items()}

        tree_nodes = build_task_tree(tasks)
        if not tree_nodes:
            self.tree.insert(
                "", "end", iid=_EMPTY_IID,
                text="タスクがありません。「+ 新しいタスク」から追加してください。",
            )
            return

        now = _now_iso()
        for flat in flatten_nodes(tree_nodes):
            task = flat.node.task
            status = statuses.get(task.status)
            is_done = status.is_done if status else False
            overdue = bool(task.due_date) and not is_done and task.due_date < now

            tags = []
            if overdue:
                tags.append("overdue")
            elif is_done:
                tags.append("done")

            parent_iid = task.parent_id or ""
            self.tree.insert(
                parent_iid, "end", iid=task.id, text=task.title, open=True,
                values=(
                    status.label if status else task.status,
                    PRIORITY_LABELS.get(task.priority, task.priority),
                    ", ".join(t.name for t in task.tags),
                    task.due_date[:10] if task.due_date else "",
                ),
                tags=tuple(tags),
            )

    # --- ドラッグ&ドロップ（同じ親配下のみ並べ替え） ------------------------
    def _on_press(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        self._drag_id = row_id if row_id != _EMPTY_IID else None

    def _on_release(self, event) -> None:
        if not self._drag_id:
            return
        active_id, self._drag_id = self._drag_id, None
        drop_id = self.tree.identify_row(event.y)
        if not drop_id or drop_id == active_id or drop_id == _EMPTY_IID:
            return

        plan = plan_tree_drag(list(self._tasks_by_id.values()), active_id, drop_id)
        if plan.get("reorder"):
            reorder_tasks(self.app.conn, plan["reorder"])
            self.refresh()
            self.on_change()

    # --- 右クリックメニュー -------------------------------------------------
    def _on_right_click(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        task = self._tasks_by_id.get(row_id)
        if task is None:
            return
        self.tree.selection_set(row_id)

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="+ サブタスクを追加", command=lambda: self._add_subtask(row_id))
        menu.add_command(label="編集", command=lambda: self._edit(task))
        if self._status_labels:
            status_menu = tk.Menu(menu, tearoff=0)
            for sid, label in self._status_labels.items():
                status_menu.add_command(
                    label=label, command=lambda s=sid, t=task: self._change_status(t.id, s)
                )
            menu.add_cascade(label="ステータス変更", menu=status_menu)
        menu.add_separator()
        menu.add_command(label="削除", command=lambda: self._delete(task))
        menu.tk_popup(event.x_root, event.y_root)

    def _on_double_click(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        task = self._tasks_by_id.get(row_id)
        if task:
            self._edit(task)

    # --- CRUD操作 -------------------------------------------------------------
    def _change_status(self, task_id: str, status_id: str) -> None:
        update_task(self.app.conn, task_id, status=status_id)
        self.refresh()
        self.on_change()

    def add_root_task(self) -> None:
        self._add_subtask(None)

    def _add_subtask(self, parent_id: str | None) -> None:
        result = ask_task_form(self.app, self.app.conn, self.project_id, parent_id=parent_id)
        if result:
            result.pop("parent_id", None)
            create_task(self.app.conn, project_id=self.project_id, parent_id=parent_id, **result)
            self.refresh()
            self.on_change()

    def _edit(self, task) -> None:
        result = ask_task_form(self.app, self.app.conn, self.project_id, task=task)
        if not result:
            return
        new_parent_id = result.pop("parent_id")
        update_task(self.app.conn, task.id, **result)
        if new_parent_id != task.parent_id:
            try:
                move_task(self.app.conn, task.id, parent_id=new_parent_id)
            except CycleError:
                messagebox.showerror(
                    "エラー", "タスクを自分自身またはその配下には移動できません。", parent=self
                )
        self.refresh()
        self.on_change()

    def _delete(self, task) -> None:
        message = f"「{task.title}」を削除しますか？配下のサブタスクも削除されます。"
        if ask_confirm(self.app, "タスクを削除", message):
            delete_task(self.app.conn, task.id)
            self.refresh()
            self.on_change()
