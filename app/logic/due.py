"""期限の判定（日付単位）。

期限日は ``YYYY-MM-DD``（時刻付きでも先頭10文字の日付のみ使う）。「期限が近い」は
本日〜3日後の4日間、「期限超過」は期限日が本日より前（当日は超過ではない）。
"""

import datetime

DUE_SOON_DAYS = 3


def today_key(today: datetime.date | None = None) -> str:
    return (today or datetime.date.today()).isoformat()


def due_soon_last_key(today: datetime.date | None = None) -> str:
    base = today or datetime.date.today()
    return (base + datetime.timedelta(days=DUE_SOON_DAYS)).isoformat()


def is_overdue(due_date: str | None, today: datetime.date | None = None) -> bool:
    return bool(due_date) and due_date[:10] < today_key(today)


def is_due_soon(due_date: str | None, today: datetime.date | None = None) -> bool:
    return bool(due_date) and today_key(today) <= due_date[:10] <= due_soon_last_key(today)
