"""タスク作成/編集モーダル（旧 client/src/components/TaskFormModal.tsx の移植）。"""

import customtkinter as ctk

from app.constants import PRIORITIES
from app.db.statuses import list_statuses
from app.db.tags import create_tag, list_tags
from app.db.tasks import list_tasks
from app.logic.tree import build_task_tree, flatten_with_depth

PRIORITY_LABELS = {"LOW": "低", "MEDIUM": "中", "HIGH": "高", "URGENT": "緊急"}


class TaskFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, project_id: str, task=None, parent_id: str | None = None):
        super().__init__(parent)
        self.conn = conn
        self.project_id = project_id
        self.task = task
        self.result: dict | None = None

        self.title("タスクを編集" if task else "新しいタスク")
        self.geometry("480x680")

        statuses = list_statuses(conn)
        all_tags = list_tags(conn)
        all_tasks = list_tasks(conn, project_id=project_id)
        exclude_id = task.id if task else None
        options = flatten_with_depth(
            build_task_tree([t for t in all_tasks if t.id != exclude_id])
        )

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="タイトル").pack(anchor="w")
        self.title_entry = ctk.CTkEntry(scroll)
        self.title_entry.pack(fill="x", pady=(0, 12))
        self.title_entry.insert(0, task.title if task else "")
        self.title_entry.focus_set()

        ctk.CTkLabel(scroll, text="説明").pack(anchor="w")
        self.description_text = ctk.CTkTextbox(scroll, height=70)
        self.description_text.pack(fill="x", pady=(0, 12))
        if task and task.description:
            self.description_text.insert("1.0", task.description)

        ctk.CTkLabel(scroll, text="ステータス").pack(anchor="w")
        status_labels = {s.id: s.label for s in statuses}
        default_status = task.status if task else (statuses[0].id if statuses else "")
        self.status_var = ctk.StringVar(value=default_status)
        self.status_menu = ctk.CTkOptionMenu(
            scroll,
            values=[s.label for s in statuses] or ["(ステータス未設定)"],
            command=lambda label: self.status_var.set(
                next((sid for sid, lbl in status_labels.items() if lbl == label), "")
            ),
        )
        if default_status in status_labels:
            self.status_menu.set(status_labels[default_status])
        self.status_menu.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(scroll, text="優先度").pack(anchor="w")
        self.priority_var = ctk.StringVar(value=task.priority if task else "MEDIUM")
        self.priority_menu = ctk.CTkOptionMenu(
            scroll,
            values=[PRIORITY_LABELS[p] for p in PRIORITIES],
            command=lambda label: self.priority_var.set(
                next(p for p in PRIORITIES if PRIORITY_LABELS[p] == label)
            ),
        )
        self.priority_menu.set(PRIORITY_LABELS[self.priority_var.get()])
        self.priority_menu.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(scroll, text="開始日 (YYYY-MM-DD)").pack(anchor="w")
        self.start_date_entry = ctk.CTkEntry(scroll)
        self.start_date_entry.pack(fill="x", pady=(0, 12))
        if task and task.start_date:
            self.start_date_entry.insert(0, task.start_date[:10])

        ctk.CTkLabel(scroll, text="期限 (YYYY-MM-DD)").pack(anchor="w")
        self.due_date_entry = ctk.CTkEntry(scroll)
        self.due_date_entry.pack(fill="x", pady=(0, 12))
        if task and task.due_date:
            self.due_date_entry.insert(0, task.due_date[:10])

        ctk.CTkLabel(scroll, text="親タスク").pack(anchor="w")
        self.parent_options: list[tuple[str | None, str]] = [(None, "(なし・最上位)")] + [
            (o.id, "　" * o.depth + o.title) for o in options
        ]
        current_parent_id = task.parent_id if task else parent_id
        current_label = next(
            (label for pid, label in self.parent_options if pid == current_parent_id),
            "(なし・最上位)",
        )
        self.parent_menu = ctk.CTkOptionMenu(
            scroll, values=[label for _, label in self.parent_options]
        )
        self.parent_menu.set(current_label)
        self.parent_menu.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(scroll, text="タグ").pack(anchor="w")
        self.tag_row = ctk.CTkFrame(scroll, fg_color="transparent")
        self.tag_row.pack(fill="x", pady=(0, 4))
        selected_tag_ids = {t.id for t in (task.tags if task else [])}
        self._tag_vars: dict[str, ctk.BooleanVar] = {}
        for tag in all_tags:
            self._add_tag_checkbox(tag.id, tag.name, tag.id in selected_tag_ids)

        new_tag_row = ctk.CTkFrame(scroll, fg_color="transparent")
        new_tag_row.pack(fill="x", pady=(0, 12))
        self.new_tag_entry = ctk.CTkEntry(new_tag_row, placeholder_text="新しいタグ")
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(new_tag_row, text="追加", width=60, command=self._add_tag).pack(side="left")

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 20))
        ctk.CTkButton(
            button_row,
            text="キャンセル",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(button_row, text="保存" if task else "作成", command=self._submit).pack(
            side="left", padx=6
        )

        self.transient(parent)
        self.grab_set()

    def _add_tag_checkbox(self, tag_id: str, name: str, checked: bool) -> None:
        var = ctk.BooleanVar(value=checked)
        self._tag_vars[tag_id] = var
        ctk.CTkCheckBox(self.tag_row, text=name, variable=var).pack(side="left", padx=(0, 8))

    def _add_tag(self) -> None:
        name = self.new_tag_entry.get().strip()
        if not name:
            return
        tag = create_tag(self.conn, name)
        self._add_tag_checkbox(tag.id, tag.name, True)
        self.new_tag_entry.delete(0, "end")

    def _submit(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            return
        parent_label = self.parent_menu.get()
        parent_id = next(
            (pid for pid, label in self.parent_options if label == parent_label), None
        )
        self.result = {
            "title": title,
            "description": self.description_text.get("1.0", "end").strip() or None,
            "status": self.status_var.get() or None,
            "priority": self.priority_var.get(),
            "start_date": self.start_date_entry.get().strip() or None,
            "due_date": self.due_date_entry.get().strip() or None,
            "tag_ids": [tid for tid, var in self._tag_vars.items() if var.get()],
            "parent_id": parent_id,
        }
        self.destroy()


def ask_task_form(
    parent, conn, project_id: str, task=None, parent_id: str | None = None
) -> dict | None:
    dialog = TaskFormDialog(parent, conn, project_id, task=task, parent_id=parent_id)
    parent.wait_window(dialog)
    return dialog.result
