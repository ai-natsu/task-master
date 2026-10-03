"""ダッシュボード画面（旧 client/src/pages/Dashboard.tsx の移植）。"""


import customtkinter as ctk

from app.db.projects import list_projects
from app.db.stats import get_stats
from app.db.statuses import list_statuses
from app.db.tasks import list_tasks
from app.i18n import format_date, t
from app.logic.due import is_due_soon, is_overdue
from app.ui import theme
from app.ui.widgets.badges import priority_badge
from app.ui.widgets.ellipsis import EllipsisLabel
from app.ui.widgets.stats_cards import render_breakdown_panels


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
        self._stat_card(cards_row, t("プロジェクト数"), str(len(projects)))
        self._stat_card(cards_row, t("直近7日の完了数"), str(stats["completedLast7Days"]))
        self._stat_card(cards_row, t("タスク総数"), str(stats["total"]))
        self._stat_card(cards_row, t("完了率"), f"{stats['completionRate']}%")
        self._stat_card(cards_row, t("期限超過"), str(stats["overdue"]), accent="#dc2626")
        self._stat_card(
            cards_row, t("期限が近い（3日後まで）"), str(stats["dueSoon"]), accent="#d97706"
        )

        overdue = sorted(
            (
                task for task in tasks
                if task.status not in done_ids and is_overdue(task.due_date)
            ),
            key=lambda task: task.due_date,
        )[:8]
        upcoming = sorted(
            (
                task for task in tasks
                if task.status not in done_ids and is_due_soon(task.due_date)
            ),
            key=lambda task: task.due_date,
        )[:8]

        lists_row = ctk.CTkFrame(self, fg_color="transparent")
        lists_row.pack(fill="x", pady=(0, 16))
        lists_row.grid_columnconfigure((0, 1), weight=1)
        self._task_list(lists_row, t("期限超過のタスク"), overdue, projects).grid(
            row=0, column=0, sticky="nsew", padx=(0, 12)
        )
        self._task_list(lists_row, t("期限が近いタスク"), upcoming, projects).grid(
            row=0, column=1, sticky="nsew", padx=(12, 0)
        )

        render_breakdown_panels(self, stats, statuses).pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(self, text=t("プロジェクト"), font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(8, 8)
        )
        if not projects:
            ctk.CTkLabel(self, text=t("プロジェクトがありません"), text_color="gray").pack(
                anchor="w"
            )
        for project in projects:
            card = ctk.CTkFrame(
                self, fg_color=theme.CARD_BG, border_width=1, border_color=theme.CARD_BORDER,
                corner_radius=10, height=48, cursor="hand2",
            )
            card.pack(fill="x", pady=4)
            card.pack_propagate(False)
            count_label = ctk.CTkLabel(
                card, text=t("{count} 件").format(count=project.task_count),
                text_color=theme.TEXT_MUTED, font=ctk.CTkFont(size=13),
            )
            count_label.pack(side="right", padx=(8, 16))
            name_label = EllipsisLabel(
                card, text="●  " + project.name, font=ctk.CTkFont(size=13, weight="bold"),
                text_color=theme.TEXT_PRIMARY, padding=8,
            )
            name_label.pack(side="left", fill="x", expand=True, padx=(16, 0))
            for widget in (card, name_label, count_label):
                widget.bind(
                    "<Button-1>",
                    lambda _e, pid=project.id: self.app.navigate("project", project_id=pid),
                )

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
        projects_by_id = {p.id: p for p in projects}
        frame = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=theme.CARD_BG,
            border_width=1, border_color=theme.CARD_BORDER,
        )
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=16, pady=(14, 8)
        )
        if not tasks:
            ctk.CTkLabel(
                frame, text=t("該当するタスクはありません"), text_color=theme.TEXT_MUTED
            ).pack(anchor="w", padx=16, pady=(0, 14))
        # ソート済みの tasks を、プロジェクト・タスクの列がそろった表形式で表示する
        for task in tasks:
            project = projects_by_id.get(task.project_id)
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            priority_badge(row, task.priority).pack(side="left", padx=(0, 8))

            project_box = ctk.CTkFrame(row, fg_color="transparent", width=140, height=20)
            project_box.pack(side="left", padx=(0, 10))
            project_box.pack_propagate(False)
            if project is not None:
                EllipsisLabel(
                    project_box, text=f"●  {project.name}",
                    text_color=project.color, font=ctk.CTkFont(size=12, weight="bold"),
                ).pack(fill="x")

            EllipsisLabel(
                row, text=task.title, text_color=theme.TEXT_PRIMARY,
                font=ctk.CTkFont(weight="bold"), padding=8,
            ).pack(side="left", fill="x", expand=True)

            due = format_date(task.due_date)
            ctk.CTkLabel(row, text=due, text_color=theme.TEXT_MUTED).pack(side="right")
        return frame
