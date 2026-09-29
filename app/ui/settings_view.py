"""設定画面：ステータス管理（旧 client/src/pages/Settings.tsx の移植）。"""

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


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._new_color = "#f59e0b"
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="設定", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(0, 16)
        )
        ctk.CTkLabel(self, text="ステータス", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", pady=(0, 8)
        )

        self.rows_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rows_frame.pack(fill="x")

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
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.error_label.configure(text="")

        statuses = list_statuses(self.app.conn)
        for index, status in enumerate(statuses):
            row = ctk.CTkFrame(self.rows_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            up_state = "disabled" if index == 0 else "normal"
            down_state = "disabled" if index == len(statuses) - 1 else "normal"
            ctk.CTkButton(
                row, text="▲", width=28, state=up_state,
                command=lambda i=index: self._move(statuses, i, -1),
            ).pack(side="left")
            ctk.CTkButton(
                row, text="▼", width=28, state=down_state,
                command=lambda i=index: self._move(statuses, i, 1),
            ).pack(side="left", padx=(2, 8))

            ctk.CTkButton(
                row, text="", width=28, height=28, fg_color=status.color,
                hover_color=status.color, corner_radius=14,
                command=lambda s=status: self._pick_status_color(s),
            ).pack(side="left", padx=(0, 8))

            entry = ctk.CTkEntry(row)
            entry.insert(0, status.label)
            entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            entry.bind("<Return>", lambda _e, s=status, en=entry: self._rename(s, en))
            entry.bind("<FocusOut>", lambda _e, s=status, en=entry: self._rename(s, en))

            is_done_var = ctk.BooleanVar(value=status.is_done)
            ctk.CTkCheckBox(
                row, text="完了として扱う", variable=is_done_var,
                command=lambda s=status, v=is_done_var: self._toggle_done(s, v),
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                row, text="削除", width=50, fg_color="transparent",
                text_color="#dc2626", hover_color=("#fee2e2", "#450a0a"),
                command=lambda s=status: self._delete(s),
            ).pack(side="left")

    def _move(self, statuses, index: int, delta: int) -> None:
        target = index + delta
        ids = [s.id for s in statuses]
        ids[index], ids[target] = ids[target], ids[index]
        reorder_statuses(self.app.conn, ids)
        self._refresh()

    def _rename(self, status, entry: ctk.CTkEntry) -> None:
        new_label = entry.get().strip()
        if not new_label or new_label == status.label:
            entry.delete(0, "end")
            entry.insert(0, status.label)
            return
        update_status(self.app.conn, status.id, label=new_label)
        self._refresh()

    def _toggle_done(self, status, var: ctk.BooleanVar) -> None:
        update_status(self.app.conn, status.id, is_done=var.get())

    def _pick_status_color(self, status) -> None:
        _, hex_color = colorchooser.askcolor(color=status.color, parent=self.app)
        if hex_color:
            update_status(self.app.conn, status.id, color=hex_color)
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

    def _delete(self, status) -> None:
        try:
            delete_status(self.app.conn, status.id)
        except ConflictError as exc:
            self.error_label.configure(text=str(exc))
            return
        self._refresh()
