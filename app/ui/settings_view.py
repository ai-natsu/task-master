"""設定画面：ステータス遷移管理（旧 client/src/pages/Settings.tsx の移植）。"""

import tkinter.colorchooser as colorchooser

import customtkinter as ctk

from app.db.errors import ConflictError
from app.db.statuses import (
    create_status,
    delete_status,
    list_statuses,
    reorder_statuses,
    update_status,
)
from app.ui import theme


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._new_color = "#f59e0b"
        self._status_rows: dict[str, ctk.CTkFrame] = {}
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="設定", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(0, 16)
        )
        ctk.CTkLabel(
            self, text="ステータス遷移", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self,
            text=(
                "ステータス遷移を設定します。新しいステータスを追加できます。"
                "既存ステータスの削除や順番の入れ替えもできます。"
            ),
            text_color=theme.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 12))

        self.rows_frame = ctk.CTkFrame(self, fg_color="transparent")
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
        self.new_label_entry = ctk.CTkEntry(add_row, placeholder_text="新しいステータス名")
        self.new_label_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.new_label_entry.bind("<Return>", lambda _e: self._add_status())
        ctk.CTkButton(add_row, text="追加", width=60, command=self._add_status).pack(side="left")

        self._refresh()

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
            row, text="完了として扱う", variable=row.is_done_var,
            command=lambda: self._toggle_done(status_id, row.is_done_var),
        )
        row.done_check.pack(side="left", padx=(0, 8))

        row.delete_btn = ctk.CTkButton(
            row, text="削除", width=50, fg_color="transparent",
            text_color="#dc2626", hover_color=("#fee2e2", "#450a0a"),
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
            self.error_label.configure(text=str(exc))
            return
        self._refresh()
