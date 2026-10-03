"""検索/フィルタバー（旧 client/src/components/FilterBar.tsx の移植）。"""

import customtkinter as ctk

from app.constants import PRIORITIES
from app.db.statuses import list_statuses
from app.db.tags import list_tags
from app.i18n import t
from app.ui import theme
from app.ui.widgets.badges import priority_label

_BORDER = "#cbd5e1"  # 枠線の色（slate-300）


class FilterBar(ctk.CTkFrame):
    def __init__(self, master, app, on_change):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.on_change = on_change

        statuses = list_statuses(self.app.conn)
        tags = list_tags(self.app.conn)
        self._status_options: list[tuple[str | None, str]] = [(None, t("すべてのステータス"))] + [
            (s.id, s.label) for s in statuses
        ]
        self._priority_options: list[tuple[str | None, str]] = [(None, t("すべての優先度"))] + [
            (p, priority_label(p)) for p in PRIORITIES
        ]
        self._tag_options: list[tuple[str | None, str]] = [(None, t("すべてのタグ"))] + [
            (tag.id, f"#{tag.name}") for tag in tags
        ]

        self.search_entry = ctk.CTkEntry(
            self, placeholder_text=t("タスクを検索..."), width=200,
            fg_color="#ffffff", border_color=_BORDER, text_color=theme.TEXT_PRIMARY[0],
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda _e: self._notify())

        self.status_menu = self._build_menu(self._status_options)
        self.priority_menu = self._build_menu(self._priority_options)
        self.tag_menu = self._build_menu(self._tag_options)

        ctk.CTkButton(
            self,
            text=t("クリア"),
            width=50,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self.clear,
        ).pack(side="left", padx=(8, 0))

    def _build_menu(self, options: list[tuple[str | None, str]]) -> ctk.CTkOptionMenu:
        # 白背景・細い枠線のセレクト（V1 と同じ見た目）。CTkOptionMenu には枠線が無いので、
        # 枠線つきのフレームに入れて表現する。
        box = ctk.CTkFrame(
            self, fg_color="#ffffff", border_width=1, border_color=_BORDER, corner_radius=8
        )
        box.pack(side="left", padx=(0, 8))
        menu = ctk.CTkOptionMenu(
            box,
            values=[label for _, label in options],
            command=lambda _label: self._notify(),
            width=140,
            fg_color="#ffffff",
            button_color="#ffffff",
            button_hover_color="#f1f5f9",
            text_color=theme.TEXT_PRIMARY[0],
            dropdown_fg_color="#ffffff",
            dropdown_text_color=theme.TEXT_PRIMARY[0],
            dropdown_hover_color="#eef2ff",
        )
        menu.set(options[0][1])
        menu.pack(padx=1, pady=1)
        return menu

    def _resolve(
        self, menu: ctk.CTkOptionMenu, options: list[tuple[str | None, str]]
    ) -> str | None:
        current_label = menu.get()
        return next((value for value, label in options if label == current_label), None)

    def _notify(self) -> None:
        self.on_change(self.get_filters())

    def get_filters(self) -> dict:
        return {
            "search": self.search_entry.get().strip() or None,
            "status": self._resolve(self.status_menu, self._status_options),
            "priority": self._resolve(self.priority_menu, self._priority_options),
            "tag_id": self._resolve(self.tag_menu, self._tag_options),
        }

    def clear(self) -> None:
        self.search_entry.delete(0, "end")
        self.status_menu.set(self._status_options[0][1])
        self.priority_menu.set(self._priority_options[0][1])
        self.tag_menu.set(self._tag_options[0][1])
        self._notify()
