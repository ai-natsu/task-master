"""プロジェクト詳細画面（旧 client/src/pages/ProjectView.tsx の移植）。

カンバン/ガントの切替はフェーズ6〜7で追加する。現時点ではツリー表示のみ。
"""

import customtkinter as ctk

from app.db.projects import get_project
from app.ui.widgets.task_tree_widget import TaskTreeWidget


class ProjectView(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
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
            header, text="+ 新しいタスク", command=lambda: self.tree_widget.add_root_task()
        ).pack(side="right")

        self.tree_widget = TaskTreeWidget(
            self,
            app=self.app,
            project_id=self.project_id,
            on_change=self.app.sidebar.refresh_projects,
        )
        self.tree_widget.grid(row=1, column=0, sticky="nsew")
