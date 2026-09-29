"""汎用確認ダイアログ（旧 client/src/components/ConfirmDialog.tsx の移植）。"""

import customtkinter as ctk


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, confirm_label: str = "削除する"):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x180")
        self.resizable(False, False)
        self.confirmed = False

        ctk.CTkLabel(self, text=message, wraplength=330, justify="left").pack(
            padx=24, pady=(24, 16), fill="both", expand=True
        )

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 20))
        ctk.CTkButton(
            button_row,
            text="キャンセル",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self._on_cancel,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            button_row,
            text=confirm_label,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=self._on_confirm,
        ).pack(side="left", padx=6)

        self.transient(parent)
        self.grab_set()

    def _on_confirm(self) -> None:
        self.confirmed = True
        self.destroy()

    def _on_cancel(self) -> None:
        self.confirmed = False
        self.destroy()


def ask_confirm(parent, title: str, message: str, confirm_label: str = "削除する") -> bool:
    dialog = ConfirmDialog(parent, title, message, confirm_label)
    parent.wait_window(dialog)
    return dialog.confirmed
