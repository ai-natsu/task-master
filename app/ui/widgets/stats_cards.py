"""統計カード＋内訳バー（旧 client/src/components/StatsCards.tsx の移植）。"""

import customtkinter as ctk

from app.constants import PRIORITIES
from app.db.stats import get_stats
from app.db.statuses import list_statuses
from app.i18n import t
from app.ui import theme
from app.ui.widgets.badges import PRIORITY_COLORS, priority_label


def build_stat_card(parent, label: str, value, accent: str | None = None) -> ctk.CTkFrame:
    card = ctk.CTkFrame(
        parent, corner_radius=14, fg_color=theme.CARD_BG,
        border_width=1, border_color=theme.CARD_BORDER,
    )
    ctk.CTkLabel(
        card, text=label, text_color=theme.TEXT_MUTED, font=ctk.CTkFont(size=12, weight="bold")
    ).pack(anchor="w", padx=16, pady=(14, 0))
    ctk.CTkLabel(
        card,
        text=str(value),
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=accent or theme.TEXT_PRIMARY,
    ).pack(anchor="w", padx=16, pady=(2, 14))
    return card


def render_stat_cards_row(parent, stats: dict) -> ctk.CTkFrame:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=(0, 12))
    build_stat_card(row, t("タスク総数"), stats["total"]).pack(
        side="left", fill="both", expand=True, padx=(0, 6)
    )
    build_stat_card(row, t("完了率"), f"{stats['completionRate']}%", accent="#059669").pack(
        side="left", fill="both", expand=True, padx=6
    )
    build_stat_card(
        row, t("期限超過"), stats["overdue"], accent="#dc2626" if stats["overdue"] > 0 else None
    ).pack(side="left", fill="both", expand=True, padx=6)
    build_stat_card(row, t("期限が近い（3日後まで）"), stats["dueSoon"], accent="#d97706").pack(
        side="left", fill="both", expand=True, padx=(6, 0)
    )
    return row


def _bar_row(parent, label: str, color: str, count: int, total: int) -> None:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=4)
    ctk.CTkLabel(
        row, text=label, text_color=color, width=70, anchor="w", font=ctk.CTkFont(weight="bold")
    ).pack(side="left")
    bar_bg = ctk.CTkFrame(row, fg_color=("#e2e8f0", "#334155"), height=8, corner_radius=4)
    bar_bg.pack(side="left", fill="x", expand=True, padx=8)
    pct = (count / total * 100) if total > 0 else 0
    if pct > 0:
        ctk.CTkFrame(bar_bg, fg_color=theme.ACCENT, height=8, corner_radius=4).place(
            relx=0, rely=0, relwidth=pct / 100, relheight=1
        )
    ctk.CTkLabel(row, text=str(count), text_color=theme.TEXT_MUTED, width=24).pack(side="left")


def render_breakdown_panels(parent, stats: dict, statuses: list) -> ctk.CTkFrame:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x")
    row.grid_columnconfigure((0, 1), weight=1)

    status_panel = ctk.CTkFrame(
        row, corner_radius=14, fg_color=theme.CARD_BG,
        border_width=1, border_color=theme.CARD_BORDER,
    )
    status_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    ctk.CTkLabel(
        status_panel, text=t("ステータス別"), font=ctk.CTkFont(size=14, weight="bold")
    ).pack(anchor="w", padx=16, pady=(14, 6))
    for status in statuses:
        _bar_row(
            status_panel, status.label, status.color,
            stats["byStatus"].get(status.id, 0), stats["total"],
        )
    ctk.CTkFrame(status_panel, fg_color="transparent", height=8).pack()

    priority_panel = ctk.CTkFrame(
        row, corner_radius=14, fg_color=theme.CARD_BG,
        border_width=1, border_color=theme.CARD_BORDER,
    )
    priority_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    ctk.CTkLabel(
        priority_panel, text=t("優先度別"), font=ctk.CTkFont(size=14, weight="bold")
    ).pack(anchor="w", padx=16, pady=(14, 6))
    for priority in reversed(PRIORITIES):
        _bar_row(
            priority_panel, priority_label(priority), PRIORITY_COLORS[priority][1],
            stats["byPriority"].get(priority, 0), stats["total"],
        )
    ctk.CTkFrame(priority_panel, fg_color="transparent", height=8).pack()

    return row


class StatsCardsPanel(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str | None = None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self.refresh()

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        stats = get_stats(self.app.conn, project_id=self.project_id)
        statuses = list_statuses(self.app.conn)
        render_stat_cards_row(self, stats)
        render_breakdown_panels(self, stats, statuses)
