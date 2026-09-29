"""プロジェクト一覧画面（旧 client/src/pages/ProjectsList.tsx の移植）。"""

import customtkinter as ctk

from app.db.projects import create_project, delete_project, list_projects, update_project
from app.db.tasks import list_tasks
from app.ui.widgets.confirm_dialog import ask_confirm
from app.ui.widgets.project_form_dialog import ask_project_form


class ProjectsListView(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._show_archived = ctk.BooleanVar(value=False)
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        title = ctk.CTkLabel(
            header, text="プロジェクト一覧", font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left")
        ctk.CTkButton(header, text="+ 新しいプロジェクト", command=self._create).pack(side="right")

        ctk.CTkCheckBox(
            self,
            text="アーカイブ済みも表示",
            variable=self._show_archived,
            command=self._refresh_list,
        ).pack(anchor="w", pady=(0, 12))

        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)
        self._refresh_list()

    def _refresh_list(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        projects = list_projects(self.app.conn, include_archived=self._show_archived.get())
        if not projects:
            ctk.CTkLabel(self.list_frame, text="プロジェクトがありません", text_color="gray").pack(
                anchor="w"
            )
            return

        for project in projects:
            row = ctk.CTkFrame(self.list_frame, corner_radius=10)
            row.pack(fill="x", pady=4)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(top, text="●", text_color=project.color, width=16).pack(side="left")
            name_btn = ctk.CTkButton(
                top,
                text=project.name,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                anchor="w",
                command=lambda pid=project.id: self.app.navigate("project", project_id=pid),
            )
            name_btn.pack(side="left")
            if project.archived:
                ctk.CTkLabel(
                    top, text="アーカイブ済み", fg_color="#e2e8f0", text_color="#475569",
                    corner_radius=8, padx=8,
                ).pack(side="left", padx=8)

            ctk.CTkButton(
                top, text="編集", width=60, fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"),
                command=lambda p=project: self._edit(p),
            ).pack(side="right")
            archive_label = "復元" if project.archived else "アーカイブ"
            ctk.CTkButton(
                top, text=archive_label, width=70, fg_color="transparent",
                text_color="#d97706", hover_color=("#fef3c7", "#451a03"),
                command=lambda p=project: self._toggle_archive(p),
            ).pack(side="right")
            ctk.CTkButton(
                top, text="削除", width=60, fg_color="transparent",
                text_color="#dc2626", hover_color=("#fee2e2", "#450a0a"),
                command=lambda p=project: self._delete(p),
            ).pack(side="right")

            if project.description:
                ctk.CTkLabel(row, text=project.description, text_color="gray", anchor="w").pack(
                    fill="x", padx=16
                )
            ctk.CTkLabel(
                row, text=f"タスク {project.task_count} 件", text_color="gray", anchor="w"
            ).pack(fill="x", padx=16, pady=(0, 12))

    def _create(self) -> None:
        result = ask_project_form(self.app)
        if result:
            create_project(self.app.conn, **result)
            self._refresh_list()
            self.app.sidebar.refresh_projects()

    def _edit(self, project) -> None:
        result = ask_project_form(
            self.app,
            initial={
                "name": project.name,
                "description": project.description,
                "color": project.color,
            },
        )
        if result:
            update_project(self.app.conn, project.id, **result)
            self._refresh_list()
            self.app.sidebar.refresh_projects()

    def _toggle_archive(self, project) -> None:
        update_project(self.app.conn, project.id, archived=not project.archived)
        self._refresh_list()
        self.app.sidebar.refresh_projects()

    def _delete(self, project) -> None:
        task_count = len(list_tasks(self.app.conn, project_id=project.id))
        message = f"「{project.name}」を削除しますか？配下の{task_count}件のタスクも削除されます。"
        if ask_confirm(self.app, "プロジェクトを削除", message):
            delete_project(self.app.conn, project.id)
            self._refresh_list()
            self.app.sidebar.refresh_projects()
