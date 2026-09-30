"""tkcalendar(DateEntry)の見た目を調整する共通ヘルパー。

- ポップアップカレンダーの土曜=青、日曜・祝日=赤の色付け
- カレンダーを開くドロップダウンボタンを、既定の細い矢印からカレンダー
  アイコンの正方形ボタンに差し替える

tkcalendarの`weekenddays`/`weekendbackground`は土日をまとめて1色にしか
塗れないため、`calevent_create`+`tag_config`で日付ごとに個別の色を付ける。
月を移動する度に`<<CalendarMonthChanged>>`で表示中の月だけ塗り直す
（全期間を事前に塗ると量が膨大になるため）。
"""

import calendar as _calendar_module
import datetime
from collections.abc import Callable
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk
from tkcalendar import DateEntry

_SATURDAY_TAG = "saturday"
_HOLIDAY_TAG = "holiday"

_DROPDOWN_ELEMENT = "Calendar.rightdownarrow"
_dropdown_icon_ref: ImageTk.PhotoImage | None = None  # GC対策で参照を保持


def apply_weekend_holiday_styles(
    entry: DateEntry, get_holiday_dates: Callable[[], set[str]]
) -> None:
    """entry: 色付け対象のDateEntry。
    get_holiday_dates: 呼び出す度に最新の祝日日付("YYYY-MM-DD"の集合)を返す
    関数（設定画面での祝日変更を都度反映するため、値ではなく関数で渡す）。
    """
    cal = entry._calendar
    cal.tag_config(_SATURDAY_TAG, background="#eff6ff", foreground="#2563eb")
    cal.tag_config(_HOLIDAY_TAG, background="#fef2f2", foreground="#dc2626")

    def _retag(_event=None) -> None:
        month, year = cal.get_displayed_month()
        holiday_dates = get_holiday_dates()
        cal.calevent_remove("all")
        _, days_in_month = _calendar_module.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            d = datetime.date(year, month, day)
            if d.isoformat() in holiday_dates or d.weekday() == 6:
                cal.calevent_create(d, "", _HOLIDAY_TAG)
            elif d.weekday() == 5:
                cal.calevent_create(d, "", _SATURDAY_TAG)

    cal.bind("<<CalendarMonthChanged>>", _retag)
    _retag()


def _make_calendar_icon(size: int, color: str) -> Image.Image:
    """正方形のカレンダーアイコン(輪郭+上部の2本のタブ+ヘッダー罫線)を描く。"""
    scale = 6
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = s * 0.12
    top = s * 0.22
    line_width = max(round(s * 0.045), 1)

    tab_w = s * 0.07
    for cx in (s * 0.30, s * 0.70):
        draw.rounded_rectangle(
            [cx - tab_w / 2, s * 0.06, cx + tab_w / 2, top + s * 0.06],
            radius=tab_w / 2, fill=color,
        )

    draw.rounded_rectangle(
        [margin, top, s - margin, s - margin], radius=s * 0.10,
        outline=color, width=line_width,
    )
    header_y = top + (s - margin - top) * 0.30
    draw.line(
        [margin + line_width / 2, header_y, s - margin - line_width / 2, header_y],
        fill=color, width=line_width,
    )
    return img.resize((size, size), Image.LANCZOS)


def _swap_downarrow(layout: list) -> list:
    new_layout = []
    for name, opts in layout:
        opts = dict(opts)
        if "downarrow" in name:
            name = _DROPDOWN_ELEMENT
        if "children" in opts:
            opts["children"] = _swap_downarrow(opts["children"])
        new_layout.append((name, opts))
    return new_layout


def apply_calendar_dropdown_icon(entry: DateEntry) -> None:
    """DateEntryのドロップダウン矢印を、正方形のカレンダーアイコンに差し替える。

    ttkの要素(element)はプロセス全体で共有されるため、画像要素の作成は最初の
    呼び出し時に一度だけ行う。一方でDateEntryは、生成直後に一度だけ自動発火
    する`<<ThemeChanged>>`（および将来の実際のテーマ変更）の度に、内部の
    `_setup_style()`で「DateEntry」スタイルのlayoutをCombobox既定へ丸ごと
    リセットしてしまう。呼び出し直後に一度差し替えるだけでは、その直後の
    自動発火で元の矢印に戻ってしまうため、`_setup_style()`自体をラップして
    「本来の処理の直後に必ず差し替えを再適用する」ようにする。
    """
    global _dropdown_icon_ref
    style = ttk.Style(entry)
    if _DROPDOWN_ELEMENT not in style.element_names():
        icon = _make_calendar_icon(size=26, color="#6366f1")
        _dropdown_icon_ref = ImageTk.PhotoImage(icon)
        style.element_create(
            _DROPDOWN_ELEMENT, "image", _dropdown_icon_ref, border=0, sticky=""
        )

    def _apply_swap() -> None:
        style.layout("DateEntry", _swap_downarrow(style.layout("DateEntry")))

    original_setup_style = entry._setup_style

    def _patched_setup_style(event=None):
        original_setup_style(event)
        _apply_swap()

    entry._setup_style = _patched_setup_style
    _apply_swap()
