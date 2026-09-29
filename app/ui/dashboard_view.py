"""ダッシュボード画面（旧 client/src/pages/Dashboard.tsx の移植）。"""

import datetime

import customtkinter as ctk

from app.db.projects import list_projects
from app.db.stats import get_stats
from app.db.statuses import list_statuses
from app.db.tasks import list_tasks
from app.ui import theme
from app.ui.widgets.badges import priority_badge
from app.ui.widgets.stats_cards import render_breakdown_panels


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self) -> None:
        conn = self.app.conn
        stats = get_stats(conn)
        statuses = list_statuses(conn)
        done_ids = {s.id for s in statuses if s.is_done}
        projects = list_projects(conn)
        tasks = list_tasks(conn)

        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 16))
        self._stat_card(cards_row, "プロジェクト数", str(len(projects)))
        self._stat_card(cards_row, "直近7日の完了数", str(stats["completedLast7Days"]))
        self._stat_card(cards_row, "タスク総数", str(stats["total"]))
        self._stat_card(cards_row, "完了率", f"{stats['completionRate']}%")
        self._stat_card(cards_row, "期限超過", str(stats["overdue"]), accent="#dc2626")
        self._stat_card(cards_row, "7日以内に期限", str(stats["dueSoon"]), accent="#d97706")

        now = _now_iso()
        overdue = sorted(
            (t for t in tasks if t.status not in done_ids and t.due_date and t.due_date < now),
            key=lambda t: t.due_date,
        )[:8]
        upcoming = sorted(
            (t for t in tasks if t.status not in done_ids and t.due_date and t.due_date >= now),
            key=lambda t: t.due_date,
        )[:8]

        lists_row = ctk.CTkFrame(self, fg_color="transparent")
        lists_row.pack(fill="x", pady=(0, 16))
        lists_row.grid_columnconfigure((0, 1), weight=1)
        self._task_list(lists_row, "期限超過のタスク", overdue, projects).grid(
            row=0, column=0, sticky="nsew", padx=(0, 12)
        )
        self._task_list(lists_row, "期限が近いタスク", upcoming, projects).grid(
            row=0, column=1, sticky="nsew", padx=(12, 0)
        )

        render_breakdown_panels(self, stats, statuses).pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(self, text="プロジェクト", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(8, 8)
        )
        if not projects:
            ctk.CTkLabel(self, text="プロジェクトがありません", text_color="gray").pack(anchor="w")
        for project in projects:
            ctk.CTkButton(
                self,
                text=f"●  {project.name}    {project.task_count} 件",
                fg_color=theme.CARD_BG,
                text_color=theme.TEXT_PRIMARY,
                hover_color=("#eef2ff", "#312e81"),
                border_width=1,
                border_color=theme.CARD_BORDER,
                corner_radius=10,
                anchor="w",
                height=48,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda pid=project.id: self.app.navigate("project", project_id=pid),
            ).pack(fill="x", pady=4)

    def _stat_card(self, parent, label, value, accent=None):
        card = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=theme.CARD_BG,
            border_width=1, border_color=theme.CARD_BORDER,
        )
        card.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkLabel(
            card, text=label, text_color=theme.TEXT_MUTED, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=16, pady=(14, 0))
        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=accent or theme.TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(2, 14))
        return card

    def _task_list(self, parent, title, tasks, projects):
        project_names = {p.id: p.name for p in projects}
        frame = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=theme.CARD_BG,
            border_width=1, border_color=theme.CARD_BORDER,
        )
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=16, pady=(14, 8)
        )
        if not tasks:
            ctk.CTkLabel(
                frame, text="該当するタスクはありません", text_color=theme.TEXT_MUTED
            ).pack(anchor="w", padx=16, pady=(0, 14))
        for t in tasks:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            priority_badge(row, t.priority).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                row, text=t.title, anchor="w", text_color=theme.TEXT_PRIMARY,
                font=ctk.CTkFont(weight="bold"),
            ).pack(side="left", fill="x", expand=True)
            due = t.due_date[:10] if t.due_date else ""
            ctk.CTkLabel(
                row, text=f"{project_names.get(t.project_id, '')}  {due}",
                text_color=theme.TEXT_MUTED,
            ).pack(side="right")
        return frame
