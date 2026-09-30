"""優先度バッジ・色ピル（旧 client/src/components/Badges.tsx の移植）。"""

import customtkinter as ctk

from app.i18n import t

# 日本語を正とする定義（他モジュールで重複定義しない）。表示時は必ず
# priority_label() 経由で参照し、都度 t() で現在の言語に変換する
# （モジュール読み込み時に一度だけ辞書化すると言語切替が反映されないため）。
_PRIORITY_LABELS_JA = {"LOW": "低", "MEDIUM": "中", "HIGH": "高", "URGENT": "緊急"}
PRIORITY_COLORS = {
    "LOW": ("#e2e8f0", "#475569"),
    "MEDIUM": ("#dbeafe", "#1d4ed8"),
    "HIGH": ("#fef3c7", "#b45309"),
    "URGENT": ("#fee2e2", "#b91c1c"),
}


def priority_label(priority: str) -> str:
    return t(_PRIORITY_LABELS_JA.get(priority, priority))


def priority_badge(parent, priority: str) -> ctk.CTkLabel:
    bg, fg = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["MEDIUM"])
    return ctk.CTkLabel(
        parent,
        text=priority_label(priority),
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
