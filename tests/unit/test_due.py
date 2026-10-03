import datetime

from app.logic.due import is_due_soon, is_overdue

TODAY = datetime.date(2026, 7, 14)


def test_overdue_is_before_today_only():
    assert is_overdue("2026-07-13", TODAY)
    assert not is_overdue("2026-07-14", TODAY)  # 当日は超過ではない
    assert not is_overdue("2026-07-15", TODAY)
    assert not is_overdue(None, TODAY)


def test_due_soon_is_today_through_three_days_later():
    assert not is_due_soon("2026-07-13", TODAY)
    assert is_due_soon("2026-07-14", TODAY)
    assert is_due_soon("2026-07-17", TODAY)
    assert not is_due_soon("2026-07-18", TODAY)
    assert not is_due_soon(None, TODAY)


def test_time_part_is_ignored_and_month_boundary():
    assert is_due_soon("2026-07-17T00:00:00.000Z", TODAY)
    assert is_due_soon("2026-08-02", datetime.date(2026, 7, 30))
    assert not is_due_soon("2026-08-03", datetime.date(2026, 7, 30))
