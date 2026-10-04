"""カレンダー表示の計算（画面に依存しない純粋関数）。

自前の日付入力部品（app/ui/widgets/date_picker.py）が使う。月曜始まりで、1 か月を 6 週 × 7 日の
格子にする（前後の月の日も含める）。
"""

import datetime
import re

# 月曜始まり
WEEKDAY_NAMES = {
    "ja": ["月", "火", "水", "木", "金", "土", "日"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
MONTH_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def month_grid(year: int, month: int) -> list[list[datetime.date]]:
    """year 年 month 月を含む、6 週 × 7 日（月曜始まり）の日付の格子。"""
    first = datetime.date(year, month, 1)
    start = first - datetime.timedelta(days=first.weekday())
    return [
        [start + datetime.timedelta(days=week * 7 + day) for day in range(7)]
        for week in range(6)
    ]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """year 年 month 月から delta か月ずらした (年, 月)。"""
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def shift_year(year: int, month: int, delta: int) -> tuple[int, int]:
    """year 年 month 月から delta 年ずらした (年, 月)。1〜9999 年の範囲に収める。"""
    return min(max(year + delta, 1), 9999), month


def day_kind(day: datetime.date, holidays: set[str]) -> str | None:
    """色分けの種類。日曜・祝日は "holiday"（赤）、土曜は "saturday"（青）、それ以外は None。"""
    if day.isoformat() in holidays or day.weekday() == 6:
        return "holiday"
    if day.weekday() == 5:
        return "saturday"
    return None


def month_title(year: int, month: int, language: str) -> tuple[str, str]:
    """ヘッダーの (年, 月) の表示。日本語は「2026年」「10月」、英語は「2026」「October」。"""
    if language == "ja":
        return f"{year}年", f"{month}月"
    return str(year), MONTH_NAMES_EN[month - 1]


def parse_date(text: str) -> datetime.date | None:
    """入力された文字を日付にする。"2026-10-04"・"2026/10/4"・"2026年10月4日" を受け付ける。

    日付として正しくない文字は None。
    """
    m = re.fullmatch(r"\s*(\d{4})\s*[-/年]\s*(\d{1,2})\s*[-/月]\s*(\d{1,2})\s*日?\s*", text)
    if m is None:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
