"""サイドバー（旧 client/src/components/Sidebar.tsx の移植）。"""

import customtkinter as ctk

from app.db.projects import delete_project, list_projects, update_project
from app.db.tasks import list_tasks
from app.ui.widgets.confirm_dialog import ask_confirm
from app.ui.widgets.project_form_dialog import ask_project_form


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, width=240, corner_radius=0)
        self.app = app
        self.grid_propagate(False)

        ctk.CTkLabel(self, text="✓ TaskMaster", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 12)
        )

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self._add_nav_button("dashboard", "📊 ダッシュボード")
        self._add_nav_button("projects", "📁 プロジェクト一覧")

        ctk.CTkLabel(self, text="プロジェクト", text_color="gray").pack(
            anchor="w", padx=16, pady=(16, 4)
        )
        self.project_list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.project_list_frame.pack(fill="x", padx=8)

        ctk.CTkFrame(self, fg_color="transparent").pack(expand=True, fill="both")

        settings_btn = ctk.CTkButton(
            self,
            text="⚙️ 設定",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=lambda: self.app.navigate("settings"),
        )
        settings_btn.pack(fill="x", padx=8, pady=(0, 16), side="bottom")
        self.nav_buttons["settings"] = settings_btn

        self.refresh_projects()

    def _add_nav_button(self, route: str, label: str) -> None:
        btn = ctk.CTkButton(
            self,
            text=label,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=lambda: self.app.navigate(route),
        )
        btn.pack(fill="x", padx=8, pady=2)
        self.nav_buttons[route] = btn

    def refresh_projects(self) -> None:
        for child in self.project_list_frame.winfo_children():
            child.destroy()
        for project in list_projects(self.app.conn):
            row = ctk.CTkFrame(self.project_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text="●", text_color=project.color, width=16).pack(side="left")

            label = ctk.CTkButton(
                row,
                text=f"{project.name} ({project.task_count})",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                anchor="w",
                command=lambda pid=project.id: self.app.navigate("project", project_id=pid),
            )
            label.pack(side="left", fill="x", expand=True)

            ctk.CTkButton(
                row,
                text="✎",
                width=24,
                fg_color="transparent",
                text_color=("gray40", "gray60"),
                hover_color=("gray85", "gray25"),
                command=lambda p=project: self._edit(p),
            ).pack(side="left")
            ctk.CTkButton(
                row,
                text="×",
                width=24,
                fg_color="transparent",
                text_color="#dc2626",
                hover_color=("#fee2e2", "#450a0a"),
                command=lambda p=project: self._delete(p),
            ).pack(side="left")

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
            self.app.refresh_current_view()

    def _delete(self, project) -> None:
        task_count = len(list_tasks(self.app.conn, project_id=project.id))
        message = f"「{project.name}」を削除しますか？配下の{task_count}件のタスクも削除されます。"
        if ask_confirm(self.app, "プロジェクトを削除", message):
            delete_project(self.app.conn, project.id)
            self.app.refresh_current_view()

    def set_active(self, route: str) -> None:
        for r, btn in self.nav_buttons.items():
            is_active = r == route
            btn.configure(fg_color=("gray75", "gray30") if is_active else "transparent")
