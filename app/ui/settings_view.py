"""設定画面：ステータス遷移・祝日管理（旧 client/src/pages/Settings.tsx の移植）。"""

import tkinter.colorchooser as colorchooser
import tkinter.filedialog as filedialog

import customtkinter as ctk
from tkcalendar import DateEntry

from app.db.errors import ConflictError, ValidationError
from app.db.holidays import (
    bulk_upsert_holidays,
    delete_holiday,
    list_holidays,
    parse_holiday_csv,
    upsert_holiday,
)
from app.db.settings import set_setting
from app.db.statuses import (
    create_status,
    delete_status,
    list_statuses,
    reorder_statuses,
    update_status,
)
from app.db.tags import count_tagged_tasks, create_tag, delete_tag, list_tags, update_tag
from app.i18n import LANGUAGES, calendar_locale, get_language, set_language, t
from app.ui import theme
from app.ui.widgets.calendar_style import (
    apply_calendar_dropdown_icon,
    apply_locale_header_format,
    apply_weekend_holiday_styles,
)
from app.ui.widgets.confirm_dialog import ask_confirm


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._new_color = "#f59e0b"
        self._new_tag_color = "#94a3b8"
        self._status_rows: dict[str, ctk.CTkFrame] = {}
        self._holiday_rows: dict[str, ctk.CTkFrame] = {}
        self._tag_rows: dict[str, ctk.CTkFrame] = {}
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=t("設定"), font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(0, 16)
        )

        ctk.CTkLabel(
            self, text="言語 / Language", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 4))
        language_row = ctk.CTkFrame(self, fg_color="transparent")
        language_row.pack(anchor="w", pady=(0, 24))
        self.language_menu = ctk.CTkOptionMenu(
            language_row, values=list(LANGUAGES.values()), command=self._on_language_change
        )
        self.language_menu.set(LANGUAGES[get_language()])
        self.language_menu.pack(side="left")

        ctk.CTkLabel(
            self, text=t("ステータス遷移"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self,
            text=t(
                "ステータス遷移を設定します。新しいステータスを追加できます。"
                "既存ステータスの削除や順番の入れ替えもできます。"
            ),
            text_color=theme.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 12))

        self.rows_frame = ctk.CTkFrame(self, fg_color="transparent", height=1)
        self.rows_frame.pack(fill="x")
        self.rows_frame.grid_columnconfigure(0, weight=1)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#dc2626")
        self.error_label.pack(anchor="w", pady=(4, 0))

        add_row = ctk.CTkFrame(self, fg_color="transparent")
        add_row.pack(fill="x", pady=(16, 0))
        self.new_color_btn = ctk.CTkButton(
            add_row, text="", width=28, height=28, fg_color=self._new_color,
            hover_color=self._new_color, corner_radius=14, command=self._pick_new_color,
        )
        self.new_color_btn.pack(side="left", padx=(0, 8))
        self.new_label_entry = ctk.CTkEntry(add_row, placeholder_text=t("新しいステータス名"))
        self.new_label_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.new_label_entry.bind("<Return>", lambda _e: self._add_status())
        ctk.CTkButton(add_row, text=t("追加"), width=60, command=self._add_status).pack(
            side="left"
        )

        # --- 祝日 ---------------------------------------------------------
        ctk.CTkLabel(
            self, text=t("祝日"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(28, 4))
        ctk.CTkLabel(
            self,
            text=t(
                "祝日を登録します。ガントチャート等での休日表示に使われます。"
                "日付が同じ行はCSV取り込み時に更新されます。"
            ),
            text_color=theme.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 12))

        holiday_header = ctk.CTkFrame(self, fg_color="transparent")
        holiday_header.pack(fill="x", padx=(38, 0))
        ctk.CTkLabel(
            holiday_header, text=t("日付"), text_color=theme.TEXT_MUTED, width=110, anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            holiday_header, text=t("名称"), text_color=theme.TEXT_MUTED, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        self.holiday_rows_frame = ctk.CTkFrame(self, fg_color="transparent", height=1)
        self.holiday_rows_frame.pack(fill="x")
        self.holiday_rows_frame.grid_columnconfigure(0, weight=1)

        self.holiday_error_label = ctk.CTkLabel(self, text="", text_color="#dc2626")
        self.holiday_error_label.pack(anchor="w", pady=(4, 0))

        holiday_add_row = ctk.CTkFrame(self, fg_color="transparent")
        holiday_add_row.pack(fill="x", pady=(12, 0))
        holiday_date_locale = calendar_locale()
        self.new_holiday_date = DateEntry(
            holiday_add_row, date_pattern="yyyy-mm-dd", width=10,
            font=(theme.FONT_FAMILY, 11), locale=holiday_date_locale,
        )
        apply_calendar_dropdown_icon(self.new_holiday_date)
        apply_locale_header_format(self.new_holiday_date, holiday_date_locale)
        apply_weekend_holiday_styles(
            self.new_holiday_date, lambda: {h.date for h in list_holidays(self.app.conn)}
        )
        self.new_holiday_date.pack(side="left", padx=(0, 8))
        self.new_holiday_name_entry = ctk.CTkEntry(
            holiday_add_row, placeholder_text=t("新しい祝日名")
        )
        self.new_holiday_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.new_holiday_name_entry.bind("<Return>", lambda _e: self._add_holiday())
        ctk.CTkButton(
            holiday_add_row, text=t("追加"), width=60, command=self._add_holiday
        ).pack(side="left")

        csv_row = ctk.CTkFrame(self, fg_color="transparent")
        csv_row.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            csv_row, text=t("CSVから読み込む"), fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER, command=self._import_holiday_csv,
        ).pack(side="left")
        self.holiday_csv_result_label = ctk.CTkLabel(csv_row, text="", text_color=theme.TEXT_MUTED)
        self.holiday_csv_result_label.pack(side="left", padx=(12, 0))

        # --- タグ -----------------------------------------------------------
        ctk.CTkLabel(
            self, text=t("タグ"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(28, 4))
        ctk.CTkLabel(
            self,
            text=t(
                "タグを管理します。プロジェクトを問わず全体で共有されます。"
                "新しいタグの作成もここから行えます。"
            ),
            text_color=theme.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 12))

        self.tag_rows_frame = ctk.CTkFrame(self, fg_color="transparent", height=1)
        self.tag_rows_frame.pack(fill="x")
        self.tag_rows_frame.grid_columnconfigure(0, weight=1)

        self.tag_error_label = ctk.CTkLabel(self, text="", text_color="#dc2626")
        self.tag_error_label.pack(anchor="w", pady=(4, 0))

        tag_add_row = ctk.CTkFrame(self, fg_color="transparent")
        tag_add_row.pack(fill="x", pady=(16, 0))
        self.new_tag_color_btn = ctk.CTkButton(
            tag_add_row, text="", width=28, height=28, fg_color=self._new_tag_color,
            hover_color=self._new_tag_color, corner_radius=14, command=self._pick_new_tag_color,
        )
        self.new_tag_color_btn.pack(side="left", padx=(0, 8))
        self.new_tag_entry = ctk.CTkEntry(tag_add_row, placeholder_text=t("新しいタグ名"))
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.new_tag_entry.bind("<Return>", lambda _e: self._add_tag())
        ctk.CTkButton(tag_add_row, text=t("追加"), width=60, command=self._add_tag).pack(
            side="left"
        )

        self._refresh()
        self._refresh_holidays()
        self._refresh_tags()

    def _on_language_change(self, label: str) -> None:
        code = next(c for c, lbl in LANGUAGES.items() if lbl == label)
        set_language(code)
        set_setting(self.app.conn, "language", code)
        self.app.rebuild()

    def _refresh(self) -> None:
        self.error_label.configure(text="")
        statuses = list_statuses(self.app.conn)
        current_ids = {s.id for s in statuses}

        for sid in list(self._status_rows.keys()):
            if sid not in current_ids:
                self._status_rows.pop(sid).destroy()

        for index, status in enumerate(statuses):
            row = self._status_rows.get(status.id)
            if row is None:
                row = self._build_row(status.id)
                self._status_rows[status.id] = row
            self._update_row(row, status, index, len(statuses))

    def _build_row(self, status_id: str) -> ctk.CTkFrame:
        """1ステータス分の行ウィジェットを一度だけ作る。

        以後の並べ替え・色/名称変更では、この行を破棄・再作成せず内容だけ
        更新する（▲▼操作時に画面が一瞬消えるちらつきを防ぐため）。
        """
        row = ctk.CTkFrame(self.rows_frame, fg_color="transparent")

        row.up_btn = ctk.CTkButton(
            row, text="▲", width=28, command=lambda: self._move(status_id, -1)
        )
        row.up_btn.pack(side="left")
        row.down_btn = ctk.CTkButton(
            row, text="▼", width=28, command=lambda: self._move(status_id, 1)
        )
        row.down_btn.pack(side="left", padx=(2, 8))

        row.color_btn = ctk.CTkButton(
            row, text="", width=28, height=28, corner_radius=14,
            command=lambda: self._pick_status_color(status_id),
        )
        row.color_btn.pack(side="left", padx=(0, 8))

        row.entry = ctk.CTkEntry(row)
        row.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        row.entry.bind("<Return>", lambda _e: self._rename(status_id, row.entry))
        row.entry.bind("<FocusOut>", lambda _e: self._rename(status_id, row.entry))

        row.is_done_var = ctk.BooleanVar(value=False)
        row.done_check = ctk.CTkCheckBox(
            row, text=t("完了として扱う"), variable=row.is_done_var,
            command=lambda: self._toggle_done(status_id, row.is_done_var),
        )
        row.done_check.pack(side="left", padx=(0, 8))

        row.delete_btn = ctk.CTkButton(
            row, text=t("削除"), width=50, fg_color="transparent",
            text_color="#9f6b6b", hover_color=("#f3e8e8", "#4a3636"),
            command=lambda: self._delete(status_id),
        )
        row.delete_btn.pack(side="left")
        return row

    def _update_row(self, row: ctk.CTkFrame, status, index: int, total: int) -> None:
        row.grid(row=index, column=0, sticky="ew", pady=2)
        row.up_btn.configure(state="disabled" if index == 0 else "normal")
        row.down_btn.configure(state="disabled" if index == total - 1 else "normal")
        row.color_btn.configure(fg_color=status.color, hover_color=status.color)
        if self.focus_get() is not row.entry and row.entry.get() != status.label:
            row.entry.delete(0, "end")
            row.entry.insert(0, status.label)
        row.is_done_var.set(status.is_done)

    def _move(self, status_id: str, delta: int) -> None:
        statuses = list_statuses(self.app.conn)
        ids = [s.id for s in statuses]
        index = ids.index(status_id)
        target = index + delta
        if not (0 <= target < len(ids)):
            return
        ids[index], ids[target] = ids[target], ids[index]
        reorder_statuses(self.app.conn, ids)
        self._refresh()

    def _rename(self, status_id: str, entry: ctk.CTkEntry) -> None:
        new_label = entry.get().strip()
        current = next((s for s in list_statuses(self.app.conn) if s.id == status_id), None)
        if current is None:
            return
        if not new_label or new_label == current.label:
            entry.delete(0, "end")
            entry.insert(0, current.label)
            return
        update_status(self.app.conn, status_id, label=new_label)

    def _toggle_done(self, status_id: str, var: ctk.BooleanVar) -> None:
        update_status(self.app.conn, status_id, is_done=var.get())

    def _pick_status_color(self, status_id: str) -> None:
        current = next((s for s in list_statuses(self.app.conn) if s.id == status_id), None)
        if current is None:
            return
        _, hex_color = colorchooser.askcolor(color=current.color, parent=self.app)
        if hex_color:
            update_status(self.app.conn, status_id, color=hex_color)
            self._refresh()

    def _pick_new_color(self) -> None:
        _, hex_color = colorchooser.askcolor(color=self._new_color, parent=self.app)
        if hex_color:
            self._new_color = hex_color
            self.new_color_btn.configure(fg_color=hex_color, hover_color=hex_color)

    def _add_status(self) -> None:
        label = self.new_label_entry.get().strip()
        if not label:
            return
        create_status(self.app.conn, label, color=self._new_color)
        self.new_label_entry.delete(0, "end")
        self._refresh()

    def _delete(self, status_id: str) -> None:
        try:
            delete_status(self.app.conn, status_id)
        except ConflictError as exc:
            self.error_label.configure(text=t(str(exc)))
            return
        self._refresh()

    # --- 祝日 ---------------------------------------------------------------
    def _refresh_holidays(self) -> None:
        self.holiday_error_label.configure(text="")
        holidays = list_holidays(self.app.conn)
        current_ids = {h.id for h in holidays}

        for hid in list(self._holiday_rows.keys()):
            if hid not in current_ids:
                self._holiday_rows.pop(hid).destroy()

        for index, holiday in enumerate(holidays):
            row = self._holiday_rows.get(holiday.id)
            if row is None:
                row = self._build_holiday_row(holiday.id)
                self._holiday_rows[holiday.id] = row
            self._update_holiday_row(row, holiday, index)

    def _build_holiday_row(self, holiday_id: str) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self.holiday_rows_frame, fg_color="transparent")

        row.date_label = ctk.CTkLabel(row, width=110, anchor="w")
        row.date_label.pack(side="left")

        row.name_entry = ctk.CTkEntry(row)
        row.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        row.name_entry.bind("<Return>", lambda _e: self._rename_holiday(holiday_id, row.name_entry))
        row.name_entry.bind(
            "<FocusOut>", lambda _e: self._rename_holiday(holiday_id, row.name_entry)
        )

        row.delete_btn = ctk.CTkButton(
            row, text=t("削除"), width=50, fg_color="transparent",
            text_color="#9f6b6b", hover_color=("#f3e8e8", "#4a3636"),
            command=lambda: self._delete_holiday(holiday_id),
        )
        row.delete_btn.pack(side="left")
        return row

    def _update_holiday_row(self, row: ctk.CTkFrame, holiday, index: int) -> None:
        row.grid(row=index, column=0, sticky="ew", pady=2)
        row.date_label.configure(text=holiday.date)
        if self.focus_get() is not row.name_entry and row.name_entry.get() != holiday.name:
            row.name_entry.delete(0, "end")
            row.name_entry.insert(0, holiday.name)

    def _rename_holiday(self, holiday_id: str, entry: ctk.CTkEntry) -> None:
        new_name = entry.get().strip()
        current = next((h for h in list_holidays(self.app.conn) if h.id == holiday_id), None)
        if current is None:
            return
        if not new_name or new_name == current.name:
            entry.delete(0, "end")
            entry.insert(0, current.name)
            return
        upsert_holiday(self.app.conn, current.date, new_name)

    def _add_holiday(self) -> None:
        name = self.new_holiday_name_entry.get().strip()
        if not name:
            return
        date = self.new_holiday_date.get_date().isoformat()
        upsert_holiday(self.app.conn, date, name)
        self.new_holiday_name_entry.delete(0, "end")
        self._refresh_holidays()

    def _delete_holiday(self, holiday_id: str) -> None:
        delete_holiday(self.app.conn, holiday_id)
        self._refresh_holidays()

    def _import_holiday_csv(self) -> None:
        path = filedialog.askopenfilename(
            title=t("祝日CSVを選択"),
            filetypes=[(t("CSVファイル"), "*.csv"), (t("すべてのファイル"), "*.*")],
        )
        if not path:
            return
        with open(path, "rb") as f:
            raw_bytes = f.read()
        try:
            rows = parse_holiday_csv(raw_bytes)
        except ValidationError as exc:
            self.holiday_csv_result_label.configure(text=t(str(exc)), text_color="#dc2626")
            return
        count = bulk_upsert_holidays(self.app.conn, rows)
        self.holiday_csv_result_label.configure(
            text=t("{count} 件を登録・更新しました").format(count=count),
            text_color=theme.TEXT_MUTED,
        )
        self._refresh_holidays()
        self._refresh()

    # --- タグ -----------------------------------------------------------------
    def _refresh_tags(self) -> None:
        self.tag_error_label.configure(text="")
        tags = list_tags(self.app.conn)
        current_ids = {tag.id for tag in tags}

        for tag_id in list(self._tag_rows.keys()):
            if tag_id not in current_ids:
                self._tag_rows.pop(tag_id).destroy()

        for index, tag in enumerate(tags):
            row = self._tag_rows.get(tag.id)
            if row is None:
                row = self._build_tag_row(tag.id)
                self._tag_rows[tag.id] = row
            self._update_tag_row(row, tag, index)

    def _build_tag_row(self, tag_id: str) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self.tag_rows_frame, fg_color="transparent")

        row.color_btn = ctk.CTkButton(
            row, text="", width=28, height=28, corner_radius=14,
            command=lambda: self._pick_tag_color(tag_id),
        )
        row.color_btn.pack(side="left", padx=(0, 8))

        row.entry = ctk.CTkEntry(row)
        row.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        row.entry.bind("<Return>", lambda _e: self._rename_tag(tag_id, row.entry))
        row.entry.bind("<FocusOut>", lambda _e: self._rename_tag(tag_id, row.entry))

        row.delete_btn = ctk.CTkButton(
            row, text=t("削除"), width=50, fg_color="transparent",
            text_color="#9f6b6b", hover_color=("#f3e8e8", "#4a3636"),
            command=lambda: self._delete_tag(tag_id),
        )
        row.delete_btn.pack(side="left")
        return row

    def _update_tag_row(self, row: ctk.CTkFrame, tag, index: int) -> None:
        row.grid(row=index, column=0, sticky="ew", pady=2)
        row.color_btn.configure(fg_color=tag.color, hover_color=tag.color)
        if self.focus_get() is not row.entry and row.entry.get() != tag.name:
            row.entry.delete(0, "end")
            row.entry.insert(0, tag.name)

    def _rename_tag(self, tag_id: str, entry: ctk.CTkEntry) -> None:
        new_name = entry.get().strip()
        current = next((tag for tag in list_tags(self.app.conn) if tag.id == tag_id), None)
        if current is None:
            return
        if not new_name or new_name == current.name:
            entry.delete(0, "end")
            entry.insert(0, current.name)
            return
        try:
            update_tag(self.app.conn, tag_id, name=new_name)
        except ConflictError as exc:
            self.tag_error_label.configure(text=t(str(exc)))
            entry.delete(0, "end")
            entry.insert(0, current.name)

    def _pick_tag_color(self, tag_id: str) -> None:
        current = next((tag for tag in list_tags(self.app.conn) if tag.id == tag_id), None)
        if current is None:
            return
        _, hex_color = colorchooser.askcolor(color=current.color, parent=self.app)
        if hex_color:
            update_tag(self.app.conn, tag_id, color=hex_color)
            self._refresh_tags()

    def _pick_new_tag_color(self) -> None:
        _, hex_color = colorchooser.askcolor(color=self._new_tag_color, parent=self.app)
        if hex_color:
            self._new_tag_color = hex_color
            self.new_tag_color_btn.configure(fg_color=hex_color, hover_color=hex_color)

    def _add_tag(self) -> None:
        name = self.new_tag_entry.get().strip()
        if not name:
            return
        try:
            create_tag(self.app.conn, name, color=self._new_tag_color)
        except ConflictError as exc:
            self.tag_error_label.configure(text=t(str(exc)))
            return
        self.new_tag_entry.delete(0, "end")
        self._refresh_tags()

    def _delete_tag(self, tag_id: str) -> None:
        current = next((tag for tag in list_tags(self.app.conn) if tag.id == tag_id), None)
        if current is None:
            return
        count = count_tagged_tasks(self.app.conn, tag_id)
        message = t(
            "「{name}」タグを削除しますか？{count}件のタスクからこのタグが外れます。"
        ).format(name=current.name, count=count)
        if ask_confirm(self.app, t("タグを削除"), message):
            delete_tag(self.app.conn, tag_id)
            self._refresh_tags()
