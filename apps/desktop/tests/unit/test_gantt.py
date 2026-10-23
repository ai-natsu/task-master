import datetime

from app.logic.gantt import compute_bar, compute_months, compute_range
from tests.factories import make_task

TODAY = datetime.date(2026, 7, 14)


def _d(s: str) -> str:
    return s  # "YYYY-MM-DD" 文字列をそのまま日付として扱う


def test_ga4a_range_covers_all_tasks_with_padding():
    tasks = [
        make_task(start_date=_d("2026-07-10"), due_date=_d("2026-07-12")),
        make_task(start_date=_d("2026-07-20"), due_date=_d("2026-07-22")),
    ]
    r = compute_range(tasks, TODAY)
    assert r.range_start.isoformat() == "2026-07-07"
    assert r.days[-1].isoformat() == "2026-07-29"
    assert len(r.days) == 23


def test_ga4b_range_extends_backward_to_include_today():
    tasks = [make_task(start_date=_d("2026-08-01"), due_date=_d("2026-08-02"))]
    r = compute_range(tasks, TODAY)
    assert r.range_start.isoformat() == "2026-07-11"


def test_ga4c_range_extends_forward_to_include_today():
    tasks = [make_task(start_date=_d("2026-06-01"), due_date=_d("2026-06-02"))]
    r = compute_range(tasks, TODAY)
    assert r.days[-1].isoformat() == "2026-07-21"


def test_ga4d_no_dated_tasks_falls_back_to_two_week_window():
    tasks = [make_task(start_date=None, due_date=None)]
    r = compute_range(tasks, TODAY)
    assert r.range_start.isoformat() == "2026-07-11"
    assert r.days[-1].isoformat() == "2026-08-03"


def test_ga4e_empty_task_list_does_not_crash():
    r = compute_range([], TODAY)
    assert len(r.days) > 0


def test_ga4f_days_are_consecutive_from_range_start():
    tasks = [make_task(due_date=_d("2026-07-20"))]
    r = compute_range(tasks, TODAY)
    assert r.days[0] == r.range_start
    assert r.days[1].isoformat() == "2026-07-12"


RANGE_START = datetime.date(2026, 7, 7)


def test_ga1_both_dates_span_inclusive():
    task = make_task(start_date=_d("2026-07-10"), due_date=_d("2026-07-12"))
    bar = compute_bar(task, RANGE_START)
    assert bar.offset_days == 3
    assert bar.span_days == 3


def test_ga1b_same_day_is_one_day_bar():
    task = make_task(start_date=_d("2026-07-10"), due_date=_d("2026-07-10"))
    bar = compute_bar(task, RANGE_START)
    assert bar.offset_days == 3
    assert bar.span_days == 1


def test_ga2a_due_date_only_is_one_day_bar():
    task = make_task(start_date=None, due_date=_d("2026-07-12"))
    bar = compute_bar(task, RANGE_START)
    assert bar.offset_days == 5
    assert bar.span_days == 1


def test_ga2b_start_date_only_is_one_day_bar():
    task = make_task(start_date=_d("2026-07-09"), due_date=None)
    bar = compute_bar(task, RANGE_START)
    assert bar.offset_days == 2
    assert bar.span_days == 1


def test_ga3_no_dates_means_no_bar():
    task = make_task(start_date=None, due_date=None)
    assert compute_bar(task, RANGE_START) is None


def test_ga3b_negative_offset_before_range_start():
    task = make_task(start_date=_d("2026-07-05"), due_date=_d("2026-07-06"))
    bar = compute_bar(task, RANGE_START)
    assert bar.offset_days == -2


def test_ga6_groups_consecutive_days_by_month():
    days = [datetime.date(2026, 7, 30), datetime.date(2026, 7, 31), datetime.date(2026, 8, 1)]
    groups = compute_months(days)
    assert [(g.label, g.count) for g in groups] == [("2026年7月", 2), ("2026年8月", 1)]


def test_ga6b_empty_days_yields_empty_groups():
    assert compute_months([]) == []
