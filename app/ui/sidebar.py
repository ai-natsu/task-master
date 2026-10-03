"""サイドバー（旧 client/src/components/Sidebar.tsx の移植）。"""

import customtkinter as ctk

from app.db.projects import delete_project, list_projects, update_project
from app.db.tasks import list_tasks
from app.i18n import t
from app.ui import theme
from app.ui.widgets.confirm_dialog import ask_confirm
from app.ui.widgets.project_form_dialog import ask_project_form

_NAV_FONT_SIZE = 15
_NAV_HEIGHT = 44
_NAV_CORNER = 10


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(
            master,
            width=272,
            corner_radius=0,
            fg_color=theme.SIDEBAR_BG,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        self.app = app
        self.grid_propagate(False)

        logo_row = ctk.CTkFrame(self, fg_color="transparent")
        logo_row.pack(anchor="w", padx=20, pady=(24, 16))
        # "✓"はYu Gothic UIに無い/薄いグリフのため、太字が確実に効く
        # Segoe UI Symbolで別ラベルにしてタイトルとの見た目のズレを防ぐ。
        ctk.CTkLabel(
            logo_row, text="✓", font=ctk.CTkFont(family="Segoe UI Symbol", size=20, weight="bold"),
            text_color=theme.ACCENT,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            logo_row, text="TaskMaster", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=theme.ACCENT,
        ).pack(side="left")

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self._add_nav_button("dashboard", "📊  " + t("ダッシュボード"))
        self._add_nav_button("projects", "📁  " + t("プロジェクト一覧"))

        ctk.CTkLabel(
            self, text=t("プロジェクト"), text_color="gray", font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=20, pady=(20, 6))
        self.project_list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.project_list_frame.pack(fill="x", padx=10)

        ctk.CTkFrame(self, fg_color="transparent").pack(expand=True, fill="both")

        settings_btn = ctk.CTkButton(
            self,
            text="⚙️  " + t("設定"),
            height=_NAV_HEIGHT,
            corner_radius=_NAV_CORNER,
            font=ctk.CTkFont(size=_NAV_FONT_SIZE),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=lambda: self.app.navigate("settings"),
        )
        settings_btn.pack(fill="x", padx=10, pady=(0, 20), side="bottom")
        self.nav_buttons["settings"] = settings_btn

        self.refresh_projects()

    def _add_nav_button(self, route: str, label: str) -> None:
        btn = ctk.CTkButton(
            self,
            text=label,
            height=_NAV_HEIGHT,
            corner_radius=_NAV_CORNER,
            font=ctk.CTkFont(size=_NAV_FONT_SIZE),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=lambda: self.app.navigate(route),
        )
        btn.pack(fill="x", padx=10, pady=3)
        self.nav_buttons[route] = btn

    def refresh_projects(self) -> None:
        for child in self.project_list_frame.winfo_children():
            child.destroy()
        for project in list_projects(self.app.conn):
            row = ctk.CTkFrame(self.project_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row, text="●", text_color=project.color, width=20, font=ctk.CTkFont(size=16)
            ).pack(side="left")

            label = ctk.CTkButton(
                row,
                text=f"{project.name} ({project.task_count})",
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
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
                width=36,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=20, weight="bold"),
                fg_color="transparent",
                text_color=("gray30", "gray70"),
                hover_color=("gray85", "gray25"),
                command=lambda p=project: self._edit(p),
            ).pack(side="left")
            ctk.CTkButton(
                row,
                text="✕",
                width=36,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=20, weight="bold"),
                fg_color="transparent",
                text_color="#9f6b6b",
                hover_color=("#f3e8e8", "#4a3636"),
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
            on_save=lambda r: update_project(self.app.conn, project.id, **r),
        )
        if result:
            self.app.refresh_current_view()

    def _delete(self, project) -> None:
        task_count = len(list_tasks(self.app.conn, project_id=project.id))
        message = t("「{name}」を削除しますか？配下の{count}件のタスクも削除されます。").format(
            name=project.name, count=task_count
        )
        if ask_confirm(self.app, t("プロジェクトを削除"), message):
            delete_project(self.app.conn, project.id)
            self.app.refresh_current_view()

    def set_active(self, route: str) -> None:
        for r, btn in self.nav_buttons.items():
            is_active = r == route
            btn.configure(
                fg_color=("#eef2ff", "#312e81") if is_active else "transparent",
                text_color=theme.ACCENT if is_active else ("gray10", "gray90"),
            )
