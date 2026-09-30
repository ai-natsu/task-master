"""tkcalendar(DateEntry)のポップアップカレンダーに、土曜=青、日曜・祝日=赤の
色付けを適用する共通ヘルパー。

tkcalendarの`weekenddays`/`weekendbackground`は土日をまとめて1色にしか
塗れないため、`calevent_create`+`tag_config`で日付ごとに個別の色を付ける。
月を移動する度に`<<CalendarMonthChanged>>`で表示中の月だけ塗り直す
（全期間を事前に塗ると量が膨大になるため）。
"""

import calendar as _calendar_module
import datetime
from collections.abc import Callable

from tkcalendar import DateEntry

_SATURDAY_TAG = "saturday"
_HOLIDAY_TAG = "holiday"


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
