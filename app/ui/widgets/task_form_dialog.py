"""タスク作成/編集モーダル（旧 client/src/components/TaskFormModal.tsx の移植）。"""

import datetime

import customtkinter as ctk
from tkcalendar import DateEntry

from app.constants import PRIORITIES
from app.db.holidays import list_holidays
from app.db.statuses import list_statuses
from app.db.tags import create_tag, list_tags
from app.db.tasks import list_tasks
from app.i18n import calendar_locale, t
from app.logic.tree import build_task_tree, flatten_with_depth
from app.ui import theme
from app.ui.widgets.badges import priority_label
from app.ui.widgets.calendar_style import (
    apply_calendar_dropdown_icon,
    apply_weekend_holiday_styles,
)


class TaskFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, project_id: str, task=None, parent_id: str | None = None):
        super().__init__(parent)
        self.conn = conn
        self.project_id = project_id
        self.task = task
        self.result: dict | None = None

        self.title(t("タスクを編集") if task else t("新しいタスク"))
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

        ctk.CTkLabel(scroll, text=t("タイトル")).pack(anchor="w")
        self.title_entry = ctk.CTkEntry(scroll)
        self.title_entry.pack(fill="x", pady=(0, 12))
        self.title_entry.insert(0, task.title if task else "")
        self.title_entry.focus_set()

        ctk.CTkLabel(scroll, text=t("説明")).pack(anchor="w")
        self.description_text = ctk.CTkTextbox(scroll, height=70)
        self.description_text.pack(fill="x", pady=(0, 12))
        if task and task.description:
            self.description_text.insert("1.0", task.description)

        ctk.CTkLabel(scroll, text=t("ステータス")).pack(anchor="w")
        status_labels = {s.id: s.label for s in statuses}
        default_status = task.status if task else (statuses[0].id if statuses else "")
        self.status_var = ctk.StringVar(value=default_status)
        self.status_menu = ctk.CTkOptionMenu(
            scroll,
            values=[s.label for s in statuses] or [t("(ステータス未設定)")],
            command=lambda label: self.status_var.set(
                next((sid for sid, lbl in status_labels.items() if lbl == label), "")
            ),
        )
        if default_status in status_labels:
            self.status_menu.set(status_labels[default_status])
        self.status_menu.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(scroll, text=t("優先度")).pack(anchor="w")
        self.priority_var = ctk.StringVar(value=task.priority if task else "MEDIUM")
        self.priority_menu = ctk.CTkOptionMenu(
            scroll,
            values=[priority_label(p) for p in PRIORITIES],
            command=lambda label: self.priority_var.set(
                next(p for p in PRIORITIES if priority_label(p) == label)
            ),
        )
        self.priority_menu.set(priority_label(self.priority_var.get()))
        self.priority_menu.pack(fill="x", pady=(0, 12))

        self.start_date_entry, self.start_date_enabled = self._build_date_field(
            scroll, t("開始日"), task.start_date if task else None
        )
        self.due_date_entry, self.due_date_enabled = self._build_date_field(
            scroll, t("期限"), task.due_date if task else None
        )

        ctk.CTkLabel(scroll, text=t("親タスク")).pack(anchor="w")
        no_parent_label = t("(なし・最上位)")
        self.parent_options: list[tuple[str | None, str]] = [(None, no_parent_label)] + [
            (o.id, "　" * o.depth + o.title) for o in options
        ]
        current_parent_id = task.parent_id if task else parent_id
        current_label = next(
            (label for pid, label in self.parent_options if pid == current_parent_id),
            no_parent_label,
        )
        self.parent_menu = ctk.CTkOptionMenu(
            scroll, values=[label for _, label in self.parent_options]
        )
        self.parent_menu.set(current_label)
        self.parent_menu.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(scroll, text=t("タグ")).pack(anchor="w")
        self.tag_row = ctk.CTkFrame(scroll, fg_color="transparent")
        self.tag_row.pack(fill="x", pady=(0, 4))
        selected_tag_ids = {t.id for t in (task.tags if task else [])}
        self._tag_vars: dict[str, ctk.BooleanVar] = {}
        for tag in all_tags:
            self._add_tag_checkbox(tag.id, tag.name, tag.id in selected_tag_ids)

        new_tag_row = ctk.CTkFrame(scroll, fg_color="transparent")
        new_tag_row.pack(fill="x", pady=(0, 12))
        self.new_tag_entry = ctk.CTkEntry(new_tag_row, placeholder_text=t("新しいタグ"))
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(new_tag_row, text=t("追加"), width=60, command=self._add_tag).pack(
            side="left"
        )

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 20))
        ctk.CTkButton(
            button_row,
            text=t("キャンセル"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            button_row,
            text=t("保存") if task else t("作成"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self._submit,
        ).pack(
            side="left", padx=6
        )

        self.transient(parent)
        self.grab_set()

    def _build_date_field(
        self, parent, label_text: str, initial: str | None
    ) -> tuple[DateEntry, ctk.BooleanVar]:
        """日付ピッカー(tkcalendar.DateEntry)を1つ構築する。

        DateEntryはカレンダーアイコンをクリックしてのピッカー選択に加えて、
        テキスト欄に直接 "YYYY-MM-DD" 形式で入力(上書き)することもできる
        （末尾のEnter/フォーカス移動で確定）。入力欄は常に操作可能で、
        カレンダーで選択または入力を確定すると「設定する」に自動でチェックが
        入る。日付は必須項目ではないため、チェックを外すとその項目はNoneになる
        （入力欄の見た目上の値は変更できるが、送信時は無視される）。
        """
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w")
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))

        entry = DateEntry(
            row, date_pattern="yyyy-mm-dd", width=12, font=(theme.FONT_FAMILY, 11),
            locale=calendar_locale(),
        )
        if initial:
            try:
                entry.set_date(datetime.date.fromisoformat(initial[:10]))
            except ValueError:
                pass
        entry.pack(side="left", padx=(0, 10), ipady=2)
        apply_calendar_dropdown_icon(entry)
        apply_weekend_holiday_styles(
            entry, lambda: {h.date for h in list_holidays(self.conn)}
        )

        enabled_var = ctk.BooleanVar(value=initial is not None)
        # カレンダーから選択した場合は<<DateEntrySelected>>が発火するが、
        # テキスト欄に直接入力して確定した場合はこのイベントが発火しない
        # (tkcalendar側の実装上、検証は内部のvalidatecommand止まりのため)。
        # そのため確定操作(Enter/フォーカス移動)側も併せて拾う。
        def _mark_enabled(_event=None) -> None:
            enabled_var.set(True)

        entry.bind("<<DateEntrySelected>>", _mark_enabled)
        entry.bind("<Return>", _mark_enabled)
        entry.bind("<FocusOut>", _mark_enabled)

        ctk.CTkCheckBox(row, text=t("設定する"), variable=enabled_var).pack(side="left")
        return entry, enabled_var

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
            "start_date": (
                self.start_date_entry.get_date().isoformat()
                if self.start_date_enabled.get()
                else None
            ),
            "due_date": (
                self.due_date_entry.get_date().isoformat()
                if self.due_date_enabled.get()
                else None
            ),
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
