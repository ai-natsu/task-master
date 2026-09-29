"""プロジェクト詳細画面（旧 client/src/pages/ProjectView.tsx の移植）。

ツリー/カンバン/ガントの各ビューはフェーズ5〜7で実装する。
現時点ではプロジェクト情報の表示のみのプレースホルダー。
"""

import customtkinter as ctk

from app.db.projects import get_project


class ProjectView(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self._build()

    def _build(self) -> None:
        project = get_project(self.app.conn, self.project_id)
        if project is None:
            ctk.CTkLabel(self, text="プロジェクトが見つかりません").pack(anchor="w")
            return

        ctk.CTkLabel(
            self, text=project.name, font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w")
        if project.description:
            ctk.CTkLabel(self, text=project.description, text_color="gray").pack(anchor="w")
        ctk.CTkLabel(
            self,
            text="ツリー/カンバン/ガント表示は今後のフェーズで実装予定です。",
            text_color="gray",
        ).pack(anchor="w", pady=(16, 0))
