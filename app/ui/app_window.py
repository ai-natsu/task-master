"""ルートウィンドウ：サイドバー＋切替コンテンツ領域（旧 Layout.tsx の移植）。"""

import sqlite3

import customtkinter as ctk

from app.ui.dashboard_view import DashboardView
from app.ui.project_view import ProjectView
from app.ui.projects_list_view import ProjectsListView
from app.ui.settings_view import SettingsView
from app.ui.sidebar import Sidebar

_VIEWS = {
    "dashboard": DashboardView,
    "projects": ProjectsListView,
    "project": ProjectView,
    "settings": SettingsView,
}


class AppWindow(ctk.CTk):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn
        self.title("TaskMaster")
        self.geometry("1280x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, app=self)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._current_view: ctk.CTkBaseClass | None = None
        self._current_route = "dashboard"
        self._current_kwargs: dict = {}
        self.navigate("dashboard")

    def navigate(self, route: str, **kwargs) -> None:
        if self._current_view is not None:
            self._current_view.destroy()

        self._current_route = route
        self._current_kwargs = kwargs
        view_cls = _VIEWS[route]
        self._current_view = view_cls(self.content, app=self, **kwargs)
        self._current_view.grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active(route)

    def refresh_current_view(self) -> None:
        self.sidebar.refresh_projects()
        self.navigate(self._current_route, **self._current_kwargs)
