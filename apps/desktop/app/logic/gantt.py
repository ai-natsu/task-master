"""ガントチャート用の日付グリッド計算（旧 client/src/utils/gantt.ts の移植）。

date-fns の startOfDay はローカルタイムで解釈されるため、元実装のテストは
タイムゾーン依存を避ける設計になっている。Python 版は単純な date 型
（時刻・タイムゾーン情報を持たない）で日付だけを扱うことで同じ考え方を踏襲する。
"""

import datetime
from dataclasses import dataclass


def _parse_date(value: str) -> datetime.date:
    return datetime.date.fromisoformat(value[:10])


@dataclass
class GanttRange:
    range_start: datetime.date
    days: list[datetime.date]


def compute_range(tasks: list, today: datetime.date) -> GanttRange:
    """全タスクの開始日/期限を含み、today も必ず含む範囲。前後にパディングを付ける。"""
    dates: list[datetime.date] = []
    for t in tasks:
        if t.start_date:
            dates.append(_parse_date(t.start_date))
        if t.due_date:
            dates.append(_parse_date(t.due_date))

    if dates:
        min_date = min(dates)
        max_date = max(dates)
    else:
        min_date = today
        max_date = today + datetime.timedelta(days=13)

    if today < min_date:
        min_date = today
    if today > max_date:
        max_date = today

    min_date -= datetime.timedelta(days=3)
    max_date += datetime.timedelta(days=7)

    count = (max_date - min_date).days + 1
    days = [min_date + datetime.timedelta(days=i) for i in range(count)]
    return GanttRange(range_start=min_date, days=days)


@dataclass
class GanttBar:
    offset_days: int
    span_days: int


def compute_bar(task, range_start: datetime.date) -> GanttBar | None:
    """1タスク分のバー位置。開始日・期限のどちらも無ければ None（バー無し）。"""
    start = _parse_date(task.start_date) if task.start_date else None
    due = _parse_date(task.due_date) if task.due_date else None
    bar_start = start or due
    bar_end = due or start
    if bar_start is None or bar_end is None:
        return None
    return GanttBar(
        offset_days=(bar_start - range_start).days,
        span_days=(bar_end - bar_start).days + 1,
    )


@dataclass
class MonthGroup:
    label: str
    count: int


def compute_months(days: list[datetime.date]) -> list[MonthGroup]:
    """連続する同月の日付を月ヘッダー用にグルーピングする。"""
    result: list[MonthGroup] = []
    for d in days:
        label = f"{d.year}年{d.month}月"
        if result and result[-1].label == label:
            result[-1].count += 1
        else:
            result.append(MonthGroup(label=label, count=1))
    return result
