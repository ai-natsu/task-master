"""入力欄の下に赤字を出し、入力欄を赤枠にする（必須項目が未入力のときの表示）。

入力し直す（文字を入力する）と、赤字と赤枠は自動で消える。
"""

import customtkinter as ctk

from app.ui import theme

ERROR_COLOR = "#dc2626"


class FieldError:
    def __init__(self, entry: ctk.CTkEntry) -> None:
        self.entry = entry
        self._normal_border = entry.cget("border_color")
        self.label = ctk.CTkLabel(
            entry.master, text="", text_color=ERROR_COLOR, anchor="w",
            font=(theme.FONT_FAMILY, 11), height=16,
        )
        entry.bind("<KeyRelease>", self._on_key, add=True)

    def show(self, message: str) -> None:
        self.entry.configure(border_color=ERROR_COLOR)
        self.label.configure(text=message)
        self.label.pack(fill="x", after=self.entry, pady=(0, 6))
        self.entry.focus_set()

    def clear(self) -> None:
        self.entry.configure(border_color=self._normal_border)
        self.label.pack_forget()

    def _on_key(self, _event) -> None:
        if self.entry.get().strip():
            self.clear()
