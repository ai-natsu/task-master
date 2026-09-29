"""プロジェクト詳細画面（旧 client/src/pages/ProjectView.tsx の移植）。

ガント表示はフェーズ7で追加する。
"""

import customtkinter as ctk

from app.db.projects import get_project
from app.ui.widgets.kanban_board_widget import KanbanBoardWidget
from app.ui.widgets.task_tree_widget import TaskTreeWidget

_VIEW_MODES = [("tree", "ツリー"), ("kanban", "カンバン")]


class ProjectView(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self.view_mode = "tree"
        self._body: ctk.CTkBaseClass | None = None
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        project = get_project(self.app.conn, self.project_id)
        if project is None:
            label = ctk.CTkLabel(self, text="プロジェクトが見つかりません")
            label.grid(row=0, column=0, sticky="w")
            return

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", anchor="w")
        ctk.CTkLabel(
            title_box, text=project.name, font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w")
        if project.description:
            ctk.CTkLabel(title_box, text=project.description, text_color="gray").pack(anchor="w")

        ctk.CTkButton(
            header, text="+ 新しいタスク", command=self._add_root_task
        ).pack(side="right")

        self.view_switch = ctk.CTkSegmentedButton(
            header,
            values=[label for _, label in _VIEW_MODES],
            command=self._on_view_switch,
        )
        self.view_switch.set(dict(_VIEW_MODES)[self.view_mode])
        self.view_switch.pack(side="right", padx=12)

        self._show_view(self.view_mode)

    def _on_view_switch(self, label: str) -> None:
        mode = next(m for m, lbl in _VIEW_MODES if lbl == label)
        self._show_view(mode)

    def _show_view(self, mode: str) -> None:
        if self._body is not None:
            self._body.destroy()
        self.view_mode = mode

        on_change = self.app.sidebar.refresh_projects
        if mode == "kanban":
            self._body = KanbanBoardWidget(
                self, app=self.app, project_id=self.project_id, on_change=on_change
            )
        else:
            self._body = TaskTreeWidget(
                self, app=self.app, project_id=self.project_id, on_change=on_change
            )
        self._body.grid(row=1, column=0, sticky="nsew")

    def _add_root_task(self) -> None:
        self._body.add_root_task()
