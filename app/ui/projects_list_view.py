"""プロジェクト一覧画面（旧 client/src/pages/ProjectsList.tsx の移植）。"""

import customtkinter as ctk

from app.db.projects import create_project, delete_project, list_projects, update_project
from app.db.tasks import list_tasks
from app.i18n import t
from app.ui import theme
from app.ui.widgets.confirm_dialog import ask_confirm
from app.ui.widgets.ellipsis import EllipsisLabel
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
            header, text=t("プロジェクト一覧"), font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left")
        ctk.CTkButton(
            header,
            text=t("+ 新しいプロジェクト"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self._create,
        ).pack(side="right")

        ctk.CTkCheckBox(
            self,
            text=t("アーカイブ済みも表示"),
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
            ctk.CTkLabel(
                self.list_frame, text=t("プロジェクトがありません"), text_color="gray"
            ).pack(anchor="w")
            return

        for project in projects:
            row = ctk.CTkFrame(
                self.list_frame, corner_radius=14, fg_color=theme.CARD_BG,
                border_width=1, border_color=theme.CARD_BORDER,
            )
            row.pack(fill="x", pady=5)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 4))
            ctk.CTkLabel(
                top, text="●", text_color=project.color, width=16, font=ctk.CTkFont(size=14)
            ).pack(side="left")
            # 右側のボタンを先に pack して幅を確保し、残りの幅にプロジェクト名を「...」付きで収める
            ctk.CTkButton(
                top, text=t("削除"), width=60, fg_color="transparent",
                text_color="#9f6b6b", hover_color=("#f3e8e8", "#4a3636"),
                command=lambda p=project: self._delete(p),
            ).pack(side="right")
            archive_label = t("復元") if project.archived else t("アーカイブ")
            ctk.CTkButton(
                top, text=archive_label, width=70, fg_color="transparent",
                text_color="#d97706", hover_color=("#fef3c7", "#451a03"),
                command=lambda p=project: self._toggle_archive(p),
            ).pack(side="right")
            ctk.CTkButton(
                top, text=t("編集"), width=60, fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"),
                command=lambda p=project: self._edit(p),
            ).pack(side="right")
            if project.archived:
                ctk.CTkLabel(
                    top, text=t("アーカイブ済み"), fg_color="#e2e8f0", text_color="#475569",
                    corner_radius=8, padx=8,
                ).pack(side="right", padx=8)
            name_label = EllipsisLabel(
                top,
                text=project.name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=theme.TEXT_PRIMARY,
                cursor="hand2",
                padding=12,
            )
            name_label.pack(side="left", fill="x", expand=True, padx=(6, 0))
            name_label.bind(
                "<Button-1>",
                lambda _e, pid=project.id: self.app.navigate("project", project_id=pid),
            )

            if project.description:
                EllipsisLabel(
                    row, text=project.description.replace("\n", " "), text_color=theme.TEXT_MUTED,
                    padding=4,
                ).pack(fill="x", padx=16)
            ctk.CTkLabel(
                row,
                text=t("タスク {count} 件").format(count=project.task_count),
                text_color=theme.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 14))

    def _create(self) -> None:
        result = ask_project_form(
            self.app, on_save=lambda r: create_project(self.app.conn, **r)
        )
        if result:
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
            on_save=lambda r: update_project(self.app.conn, project.id, **r),
        )
        if result:
            self._refresh_list()
            self.app.sidebar.refresh_projects()

    def _toggle_archive(self, project) -> None:
        update_project(self.app.conn, project.id, archived=not project.archived)
        self._refresh_list()
        self.app.sidebar.refresh_projects()

    def _delete(self, project) -> None:
        task_count = len(list_tasks(self.app.conn, project_id=project.id))
        message = t("「{name}」を削除しますか？配下の{count}件のタスクも削除されます。").format(
            name=project.name, count=task_count
        )
        if ask_confirm(self.app, t("プロジェクトを削除"), message):
            delete_project(self.app.conn, project.id)
            self._refresh_list()
            self.app.sidebar.refresh_projects()
