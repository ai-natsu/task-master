"""カレンダー表示の計算（app/logic/calendar_grid.py）。"""

import datetime

import pytest

from app.logic.calendar_grid import (
    day_kind,
    month_grid,
    month_title,
    parse_date,
    shift_month,
    shift_year,
)


class TestMonthGrid:
    def test_is_six_weeks_of_seven_days_starting_on_monday(self):
        grid = month_grid(2026, 10)
        assert len(grid) == 6
        assert all(len(week) == 7 for week in grid)
        assert all(week[0].weekday() == 0 for week in grid)  # 月曜始まり

    def test_october_2026_layout(self):
        grid = month_grid(2026, 10)
        assert grid[0][0] == datetime.date(2026, 9, 28)  # 前月の日が先頭に入る
        assert grid[0][3] == datetime.date(2026, 10, 1)  # 10/1 は木曜
        assert grid[-1][-1] == datetime.date(2026, 11, 8)  # 翌月の日が末尾に入る

    def test_month_that_starts_on_sunday(self):
        grid = month_grid(2026, 2)  # 2026-02-01 は日曜
        assert grid[0][0] == datetime.date(2026, 1, 26)
        assert grid[0][6] == datetime.date(2026, 2, 1)

    def test_every_day_of_the_month_appears_once(self):
        days = [d for week in month_grid(2024, 2) for d in week if d.month == 2]
        assert days == [datetime.date(2024, 2, n) for n in range(1, 30)]  # うるう年


class TestShift:
    @pytest.mark.parametrize(
        "year, month, delta, expected",
        [
            (2026, 10, 1, (2026, 11)),
            (2026, 12, 1, (2027, 1)),
            (2026, 1, -1, (2025, 12)),
            (2026, 10, 25, (2028, 11)),
            (2026, 10, -22, (2024, 12)),
        ],
    )
    def test_shift_month(self, year, month, delta, expected):
        assert shift_month(year, month, delta) == expected

    def test_shift_year_keeps_the_month_and_stays_in_range(self):
        assert shift_year(2026, 10, 1) == (2027, 10)
        assert shift_year(2026, 10, -1) == (2025, 10)
        assert shift_year(9999, 1, 1) == (9999, 1)
        assert shift_year(1, 1, -1) == (1, 1)


class TestDayKind:
    HOLIDAYS = {"2026-10-12", "2026-10-10"}

    def test_sunday_is_holiday_colour(self):
        assert day_kind(datetime.date(2026, 10, 4), set()) == "holiday"

    def test_saturday_is_blue(self):
        assert day_kind(datetime.date(2026, 10, 3), set()) == "saturday"

    def test_registered_holiday_on_a_weekday(self):
        assert day_kind(datetime.date(2026, 10, 12), self.HOLIDAYS) == "holiday"

    def test_registered_holiday_on_saturday_wins(self):
        assert day_kind(datetime.date(2026, 10, 10), self.HOLIDAYS) == "holiday"

    def test_plain_weekday_has_no_colour(self):
        assert day_kind(datetime.date(2026, 10, 5), self.HOLIDAYS) is None


def test_month_title_in_each_language():
    assert month_title(2026, 10, "ja") == ("2026年", "10月")
    assert month_title(2026, 10, "en") == ("2026", "October")


class TestParseDate:
    @pytest.mark.parametrize(
        "text",
        ["2026-10-04", "2026/10/4", "2026-1-5", " 2026-10-04 ", "2026年10月4日", "2026年10月04日"],
    )
    def test_accepts_common_forms(self, text):
        assert parse_date(text) is not None

    def test_returns_the_date(self):
        assert parse_date("2026/10/4") == datetime.date(2026, 10, 4)

    @pytest.mark.parametrize(
        "text", ["", "abc", "2026-02-30", "2026-13-01", "26-10-04", "2026-10", "2026-10-04-1"]
    )
    def test_rejects_invalid_text(self, text):
        assert parse_date(text) is None
