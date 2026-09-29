"""検索/フィルタバー（旧 client/src/components/FilterBar.tsx の移植）。"""

import customtkinter as ctk

from app.constants import PRIORITIES
from app.db.statuses import list_statuses
from app.db.tags import list_tags
from app.ui.widgets.badges import PRIORITY_LABELS

_ALL_STATUSES = "すべてのステータス"
_ALL_PRIORITIES = "すべての優先度"
_ALL_TAGS = "すべてのタグ"


class FilterBar(ctk.CTkFrame):
    def __init__(self, master, app, on_change):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.on_change = on_change

        statuses = list_statuses(self.app.conn)
        tags = list_tags(self.app.conn)
        self._status_options: list[tuple[str | None, str]] = [(None, _ALL_STATUSES)] + [
            (s.id, s.label) for s in statuses
        ]
        self._priority_options: list[tuple[str | None, str]] = [(None, _ALL_PRIORITIES)] + [
            (p, PRIORITY_LABELS[p]) for p in PRIORITIES
        ]
        self._tag_options: list[tuple[str | None, str]] = [(None, _ALL_TAGS)] + [
            (t.id, f"#{t.name}") for t in tags
        ]

        self.search_entry = ctk.CTkEntry(self, placeholder_text="タスクを検索...", width=200)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _e: self._notify())

        self.status_menu = self._build_menu(self._status_options)
        self.priority_menu = self._build_menu(self._priority_options)
        self.tag_menu = self._build_menu(self._tag_options)

        ctk.CTkButton(
            self,
            text="クリア",
            width=50,
            fg_color="transparent",
            text_color=("gray40", "gray60"),
            hover_color=("gray85", "gray25"),
            command=self.clear,
        ).pack(side="left", padx=(8, 0))

    def _build_menu(self, options: list[tuple[str | None, str]]) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(
            self,
            values=[label for _, label in options],
            command=lambda _label: self._notify(),
            width=140,
        )
        menu.set(options[0][1])
        menu.pack(side="left", padx=(0, 8))
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
