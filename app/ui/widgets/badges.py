"""優先度バッジ・色ピル（旧 client/src/components/Badges.tsx の移植）。"""

import customtkinter as ctk

PRIORITY_LABELS = {"LOW": "低", "MEDIUM": "中", "HIGH": "高", "URGENT": "緊急"}
PRIORITY_COLORS = {
    "LOW": ("#e2e8f0", "#475569"),
    "MEDIUM": ("#dbeafe", "#1d4ed8"),
    "HIGH": ("#fef3c7", "#b45309"),
    "URGENT": ("#fee2e2", "#b91c1c"),
}


def priority_badge(parent, priority: str) -> ctk.CTkLabel:
    bg, fg = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["MEDIUM"])
    return ctk.CTkLabel(
        parent,
        text=PRIORITY_LABELS.get(priority, priority),
        fg_color=bg,
        text_color=fg,
        corner_radius=8,
        padx=8,
    )


def color_pill(parent, text: str, color: str) -> ctk.CTkLabel:
    """ステータス/タグ用の色ピル。実データの色をそのまま使うため動的に算出する。"""
    return ctk.CTkLabel(
        parent,
        text=text,
        fg_color=color,
        text_color="#ffffff",
        corner_radius=8,
        padx=8,
    )
