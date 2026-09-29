"""プロジェクト作成/編集モーダル（旧 client/src/components/ProjectFormModal.tsx の移植）。"""

import customtkinter as ctk

PALETTE = ["#6366f1", "#22c55e", "#ef4444", "#f59e0b", "#0ea5e9", "#a855f7", "#ec4899"]


class ProjectFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, initial: dict | None = None):
        super().__init__(parent)
        self.title("プロジェクトを編集" if initial else "新しいプロジェクト")
        self.geometry("420x440")
        self.resizable(False, False)
        self.result: dict | None = None
        self._selected_color = (initial or {}).get("color", PALETTE[0])

        ctk.CTkLabel(self, text="名前").pack(anchor="w", padx=20, pady=(20, 4))
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.pack(fill="x", padx=20)
        self.name_entry.insert(0, (initial or {}).get("name", ""))
        self.name_entry.focus_set()

        ctk.CTkLabel(self, text="説明").pack(anchor="w", padx=20, pady=(16, 4))
        self.description_text = ctk.CTkTextbox(self, height=80)
        self.description_text.pack(fill="x", padx=20)
        self.description_text.insert("1.0", (initial or {}).get("description") or "")

        ctk.CTkLabel(self, text="色").pack(anchor="w", padx=20, pady=(16, 4))
        swatch_row = ctk.CTkFrame(self, fg_color="transparent")
        swatch_row.pack(padx=20, anchor="w")
        self._swatch_buttons: dict[str, ctk.CTkButton] = {}
        for color in PALETTE:
            btn = ctk.CTkButton(
                swatch_row,
                text="",
                width=28,
                height=28,
                fg_color=color,
                hover_color=color,
                corner_radius=14,
                border_width=3 if color == self._selected_color else 0,
                border_color="#111827",
                command=lambda c=color: self._select_color(c),
            )
            btn.pack(side="left", padx=4)
            self._swatch_buttons[color] = btn

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(side="bottom", pady=20)
        ctk.CTkButton(
            button_row,
            text="キャンセル",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            button_row, text="保存" if initial else "作成", command=self._submit
        ).pack(side="left", padx=6)

        self.transient(parent)
        self.grab_set()

    def _select_color(self, color: str) -> None:
        for c, btn in self._swatch_buttons.items():
            btn.configure(border_width=3 if c == color else 0)
        self._selected_color = color

    def _submit(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            return
        self.result = {
            "name": name,
            "description": self.description_text.get("1.0", "end").strip() or None,
            "color": self._selected_color,
        }
        self.destroy()


def ask_project_form(parent, initial: dict | None = None) -> dict | None:
    dialog = ProjectFormDialog(parent, initial)
    parent.wait_window(dialog)
    return dialog.result
