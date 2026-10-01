"""タスク作成/編集モーダル（旧 client/src/components/TaskFormModal.tsx の移植）。"""

import datetime
import tkinter as tk

import customtkinter as ctk
from tkcalendar import DateEntry

from app.constants import PRIORITIES
from app.db.holidays import list_holidays
from app.db.statuses import list_statuses
from app.db.tags import count_tagged_tasks, create_tag, delete_tag, list_tags
from app.db.tasks import create_task, list_tasks
from app.i18n import calendar_locale, t
from app.logic.tree import build_task_tree, flatten_with_depth
from app.ui import theme
from app.ui.widgets.badges import priority_label
from app.ui.widgets.calendar_style import (
    apply_calendar_dropdown_icon,
    apply_locale_header_format,
    apply_weekend_holiday_styles,
)
from app.ui.widgets.confirm_dialog import ask_confirm


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
        scroll.pack(fill="both", expand=True, padx=14, pady=14)

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
        self._statuses = statuses
        status_labels = {s.id: s.label for s in statuses}
        self._status_labels = status_labels
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

        dates_row = ctk.CTkFrame(scroll, fg_color="transparent")
        dates_row.pack(fill="x")
        # 単純にpack(side="left", expand=True)を2つ並べるだけだと、両者の
        # 合計幅が収まりきらない時に後から詰んだ方(期限側)だけが極端に
        # 狭くなり中身が見切れる。grid+uniformで強制的に等幅にする。
        dates_row.grid_columnconfigure(0, weight=1, uniform="date_col")
        dates_row.grid_columnconfigure(1, weight=1, uniform="date_col")
        start_col = ctk.CTkFrame(dates_row, fg_color="transparent")
        start_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        due_col = ctk.CTkFrame(dates_row, fg_color="transparent")
        due_col.grid(row=0, column=1, sticky="nsew")

        self.start_date_entry, self.start_date_enabled = self._build_date_field(
            start_col, t("開始日"), task.start_date if task else None
        )
        self.due_date_entry, self.due_date_enabled = self._build_date_field(
            due_col, t("期限"), task.due_date if task else None
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
        self._initial_parent_label = current_label

        ctk.CTkLabel(scroll, text=t("タグ")).pack(anchor="w")
        self.tag_row = ctk.CTkFrame(scroll, fg_color="transparent", height=1)
        self.tag_row.pack(fill="x", pady=(0, 4))
        selected_tag_ids = {t.id for t in (task.tags if task else [])}
        self._tag_items: list[tuple[str, str]] = []
        self._tag_vars: dict[str, ctk.BooleanVar] = {}
        for tag in all_tags:
            self._tag_vars[tag.id] = ctk.BooleanVar(value=tag.id in selected_tag_ids)
            self._tag_items.append((tag.id, tag.name))
        # ダイアログの描画が完了する前だとtag_rowの幅がまだ確定しておらず
        # 折り返し計算を誤るため、アイドル状態(レイアウト確定後)まで遅延させる。
        self.after_idle(self._rebuild_tag_checkboxes)

        new_tag_row = ctk.CTkFrame(scroll, fg_color="transparent")
        new_tag_row.pack(fill="x", pady=(0, 12))
        self.new_tag_entry = ctk.CTkEntry(new_tag_row, placeholder_text=t("新しいタグ"))
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(new_tag_row, text=t("追加"), width=60, command=self._add_tag).pack(
            side="left"
        )

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", padx=14, pady=(0, 14))

        left_buttons = ctk.CTkFrame(button_row, fg_color="transparent")
        left_buttons.pack(side="left")
        ctk.CTkButton(
            left_buttons,
            text=t("キャンセル"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            left_buttons,
            text=t("保存") if task else t("作成"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self._submit,
        ).pack(side="left", padx=6)

        self.continue_var: ctk.BooleanVar | None = None
        if task is None:
            self.continue_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                button_row, text=t("続けて作成"), variable=self.continue_var
            ).pack(side="right", padx=6)

        self.transient(parent)
        self.grab_set()

    def _build_date_field(
        self, parent, label_text: str, initial: str | None
    ) -> tuple[DateEntry, ctk.BooleanVar]:
        """日付ピッカー(tkcalendar.DateEntry)を1つ構築する。

        DateEntryはカレンダーアイコンをクリックしてのピッカー選択に加えて、
        テキスト欄に直接 "YYYY-MM-DD" 形式で入力(上書き)することもできる
        （末尾のEnter/フォーカス移動で確定）。「有効」が外れている間は
        入力欄を無効化(グレーアウト)し、操作できないようにする。日付は必須
        項目ではないため、チェックを外すとその項目はNoneになる。
        """
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w")
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))

        locale = calendar_locale()
        entry = DateEntry(
            row, date_pattern="yyyy-mm-dd", width=12, font=(theme.FONT_FAMILY, 11),
            locale=locale,
        )
        if initial:
            try:
                entry.set_date(datetime.date.fromisoformat(initial[:10]))
            except ValueError:
                pass
        entry.pack(side="left", padx=(0, 10), ipady=2)
        apply_calendar_dropdown_icon(entry)
        apply_locale_header_format(entry, locale)
        apply_weekend_holiday_styles(
            entry, lambda: {h.date for h in list_holidays(self.conn)}
        )

        enabled_var = ctk.BooleanVar(value=initial is not None)

        def _apply_entry_state() -> None:
            entry.configure(state="normal" if enabled_var.get() else "disabled")

        # カレンダーから選択した場合は<<DateEntrySelected>>が発火するが、
        # テキスト欄に直接入力して確定した場合はこのイベントが発火しない
        # (tkcalendar側の実装上、検証は内部のvalidatecommand止まりのため)。
        # そのため確定操作(Enter/フォーカス移動)側も併せて拾う。
        def _mark_enabled(_event=None) -> None:
            enabled_var.set(True)
            _apply_entry_state()

        entry.bind("<<DateEntrySelected>>", _mark_enabled)
        entry.bind("<Return>", _mark_enabled)
        entry.bind("<FocusOut>", _mark_enabled)

        ctk.CTkCheckBox(
            row, text=t("有効"), variable=enabled_var, command=_apply_entry_state
        ).pack(side="left")
        _apply_entry_state()
        return entry, enabled_var

    def _add_tag_checkbox(self, tag_id: str, name: str, checked: bool) -> None:
        self._tag_vars[tag_id] = ctk.BooleanVar(value=checked)
        self._tag_items.append((tag_id, name))
        self._rebuild_tag_checkboxes()

    _TAG_CHECKBOX_MIN_WIDTH = 90

    def _rebuild_tag_checkboxes(self) -> None:
        """タグのチェックボックスを、幅に収まるよう複数行に折り返して並べ直す。

        CTkCheckBoxを単一行にpack(side="left")するだけだと、タグ数が増えた
        時に画面幅からはみ出して見切れてしまうため、行の残り幅を超えたら
        新しい行フレームを作って続きを詰めていく(CSSのflex-wrapに相当する
        簡易実装)。

        幅の決定は2段階に分ける: (1)まず使い捨てのチェックボックスを作って
        実際の幅を測り、(2)その結果をもとに行を確定してから本物のチェック
        ボックスをその行の下に直接作る。1回で「作る→測る→はみ出たら別の行に
        移す」とやろうとすると、Tkのウィジェットは生成後に親(master)を変更
        できないため、pack_forget()して別フレームへpack()し直しても実際には
        元の親に戻ってしまい、正しく移動しない。
        """
        for child in self.tag_row.winfo_children():
            child.destroy()

        self.tag_row.update_idletasks()
        available_width = self.tag_row.winfo_width()
        if available_width <= 1:
            available_width = 400

        widths = []
        for _tag_id, name in self._tag_items:
            probe = ctk.CTkCheckBox(
                self.tag_row, text=name, width=self._TAG_CHECKBOX_MIN_WIDTH
            )
            probe.update_idletasks()
            widths.append(probe.winfo_reqwidth() + 8)
            probe.destroy()

        row = ctk.CTkFrame(self.tag_row, fg_color="transparent")
        row.pack(fill="x", anchor="w")
        used_width = 0
        for (tag_id, name), checkbox_width in zip(self._tag_items, widths):
            if used_width + checkbox_width > available_width and used_width > 0:
                row = ctk.CTkFrame(self.tag_row, fg_color="transparent")
                row.pack(fill="x", anchor="w")
                used_width = 0
            checkbox = ctk.CTkCheckBox(
                row, text=name, variable=self._tag_vars[tag_id],
                width=self._TAG_CHECKBOX_MIN_WIDTH,
            )
            checkbox.pack(side="left", padx=(0, 8), pady=(0, 4))
            checkbox.bind(
                "<Button-3>",
                lambda e, tid=tag_id, nm=name: self._on_tag_right_click(e, tid, nm),
            )
            used_width += checkbox_width

    def _on_tag_right_click(self, event, tag_id: str, name: str) -> None:
        menu = tk.Menu(self, tearoff=0, font=(theme.FONT_FAMILY, 12))
        menu.add_command(
            label=t("削除"), command=lambda: self._delete_tag_from_form(tag_id, name)
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _delete_tag_from_form(self, tag_id: str, name: str) -> None:
        count = count_tagged_tasks(self.conn, tag_id)
        message = t(
            "「{name}」タグを削除しますか？{count}件のタスクからこのタグが外れます。"
        ).format(name=name, count=count)
        if not ask_confirm(self, t("タグを削除"), message):
            return
        delete_tag(self.conn, tag_id)
        self._tag_vars.pop(tag_id, None)
        self._tag_items = [(tid, nm) for tid, nm in self._tag_items if tid != tag_id]
        self._rebuild_tag_checkboxes()

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
        result = {
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

        if self.continue_var is not None and self.continue_var.get():
            create_task(self.conn, project_id=self.project_id, **result)
            self._reset_form()
            return

        self.result = result
        self.destroy()

    def _reset_form(self) -> None:
        """「続けて作成」用に、作成直後のフォームを新規作成時の初期状態へ戻す。"""
        self.title_entry.delete(0, "end")
        self.description_text.delete("1.0", "end")

        default_status = self._statuses[0].id if self._statuses else ""
        self.status_var.set(default_status)
        if default_status in self._status_labels:
            self.status_menu.set(self._status_labels[default_status])

        self.priority_var.set("MEDIUM")
        self.priority_menu.set(priority_label("MEDIUM"))

        for entry, enabled_var in (
            (self.start_date_entry, self.start_date_enabled),
            (self.due_date_entry, self.due_date_enabled),
        ):
            entry.configure(state="normal")
            entry.set_date(datetime.date.today())
            entry.configure(state="disabled")
            enabled_var.set(False)

        self.parent_menu.set(self._initial_parent_label)

        for var in self._tag_vars.values():
            var.set(False)

        self.title_entry.focus_set()


def ask_task_form(
    parent, conn, project_id: str, task=None, parent_id: str | None = None
) -> dict | None:
    dialog = TaskFormDialog(parent, conn, project_id, task=task, parent_id=parent_id)
    parent.wait_window(dialog)
    return dialog.result
