"""優先度バッジ・色ピル（旧 client/src/components/Badges.tsx の移植）。"""

import customtkinter as ctk

from app.i18n import t
from app.ui import theme

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


def _tint(color: str, ratio: float) -> str:
    """16進カラーを白に近づける（ピルの薄い背景色用）。"""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(*(round(c + (255 - c) * ratio) for c in (r, g, b)))


def color_pill(parent, text: str, color: str | None = None) -> ctk.CTkLabel:
    """タグ用のピル。タグの色が分かれば、その色の薄い背景＋色付きの文字（V1 と同じ）で表示する。

    色を渡さない場合（「...」の省略ピルなど）は、周囲と馴染むグレーで表示する。
    """
    if color:
        return ctk.CTkLabel(
            parent, text=text, fg_color=_tint(color, 0.85), text_color=color, corner_radius=8,
            padx=8,
        )
    return ctk.CTkLabel(
        parent,
        text=text,
        fg_color=theme.SUBTLE_BG,
        text_color=theme.TEXT_PRIMARY,
        corner_radius=8,
        padx=8,
    )
