"""入力欄の文字数を上限までに制限する（V1 の `maxlength` と同じ動作）。

上限を超えるキー入力はできず、貼り付けは上限まで切り詰める。上限は app/constants.py の LIMITS。
データ層（app/db/validation.py）でも検査するので、ここは入力の時点で気づかせるためのもの。
"""

import tkinter as tk

import customtkinter as ctk

from app.constants import LIMITS


def limit_entry(entry: ctk.CTkEntry, key: str) -> None:
    """CTkEntry の文字数を LIMITS[key] までに制限する。"""
    max_len = LIMITS[key]
    inner = entry._entry  # CTkEntry の中の tk.Entry（公開されていないが、検証の設定にはこれが必要）

    def _validate(proposed: str) -> bool:
        return len(proposed) <= max_len

    inner.configure(validate="key", validatecommand=(inner.register(_validate), "%P"))

    def _paste(_event) -> str:
        try:
            text = inner.clipboard_get()
        except tk.TclError:
            return "break"
        selected = 0
        if inner.selection_present():
            selected = abs(inner.index("sel.last") - inner.index("sel.first"))
            inner.delete("sel.first", "sel.last")
        room = max_len - len(inner.get())
        inner.insert("insert", text.replace("\n", " ")[: max(room, 0)])
        return "break" if selected >= 0 else ""

    inner.bind("<<Paste>>", _paste)


def limit_textbox(textbox: ctk.CTkTextbox, key: str) -> None:
    """CTkTextbox（複数行）の文字数を LIMITS[key] までに制限する。"""
    max_len = LIMITS[key]
    inner = textbox._textbox  # CTkTextbox の中の tk.Text

    def _length() -> int:
        return len(inner.get("1.0", "end-1c"))

    def _selection_length() -> int:
        try:
            return len(inner.get("sel.first", "sel.last"))
        except tk.TclError:
            return 0

    def _on_key(event) -> str | None:
        # 文字を入力するキー（Ctrl・Alt つきや、移動・削除のキーは対象外）
        if event.char and event.char.isprintable() and not (event.state & 0x4):
            if _length() - _selection_length() >= max_len:
                return "break"
        return None

    def _paste(_event) -> str:
        try:
            text = inner.clipboard_get()
        except tk.TclError:
            return "break"
        if _selection_length():
            inner.delete("sel.first", "sel.last")
        room = max_len - _length()
        inner.insert("insert", text[: max(room, 0)])
        return "break"

    inner.bind("<KeyPress>", _on_key, add=True)
    inner.bind("<<Paste>>", _paste)
