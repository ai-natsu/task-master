"""日付入力欄とカレンダー（app/ui/widgets/date_picker.py）。"""

import datetime
from types import SimpleNamespace

import customtkinter as ctk
import pytest

from app import i18n
from app.ui.widgets.date_picker import DatePicker

pytestmark = pytest.mark.gui


@pytest.fixture
def host(app_window):
    frame = ctk.CTkFrame(app_window)
    frame.grid(row=98, column=0)
    yield frame
    frame.destroy()


@pytest.fixture
def calls():
    return []


@pytest.fixture
def picker(host, app_window, calls):
    widget = DatePicker(
        host,
        date=datetime.date(2026, 10, 4),
        holidays=lambda: {"2026-10-12"},
        command=lambda: calls.append(1),
    )
    widget.pack()
    app_window.update()
    yield widget
    if widget._popup is not None:
        widget._popup.close()


def _cell(popup, day: datetime.date):
    for row in popup._day_labels:
        for cell in row:
            if cell._date == day and cell.cget("text") == str(day.day):
                return cell
    raise AssertionError(f"{day} のセルが見つかりません")


class TestEntry:
    def test_shows_the_given_date(self, picker):
        assert picker.entry.get() == "2026-10-04"
        assert picker.get_date() == datetime.date(2026, 10, 4)

    def test_set_date_updates_the_text(self, picker):
        picker.set_date(datetime.date(2027, 1, 31))
        assert picker.entry.get() == "2027-01-31"
        assert picker.get_date() == datetime.date(2027, 1, 31)

    def test_typed_date_is_committed_on_enter(self, picker, calls, app_window):
        picker.entry._entry.focus_force()  # キー入力は、フォーカスのある入力欄に届く
        app_window.update()
        picker.entry.delete(0, "end")
        picker.entry.insert(0, "2026/12/5")
        picker.entry._entry.event_generate("<Return>")
        assert picker.get_date() == datetime.date(2026, 12, 5)
        assert picker.entry.get() == "2026-12-05"  # 表示は ISO の形式にそろう
        assert calls == [1]

    def test_invalid_text_reverts_to_the_last_valid_date(self, picker, calls):
        picker.entry.delete(0, "end")
        picker.entry.insert(0, "2026-02-30")
        assert picker.get_date() == datetime.date(2026, 10, 4)
        assert picker.entry.get() == "2026-10-04"
        assert calls == []

    def test_disabled_picker_does_not_open_the_calendar(self, picker):
        picker.configure(state="disabled")
        picker.open_calendar()
        assert picker._popup is None
        picker.configure(state="normal")
        picker.open_calendar()
        assert picker._popup is not None


class TestCalendar:
    def test_opens_on_the_selected_month_with_the_day_highlighted(self, picker, app_window):
        picker.open_calendar()
        app_window.update()
        popup = picker._popup
        assert popup._month_label.cget("text") == "10月"
        assert popup._year_label.cget("text") == "2026年"
        assert _cell(popup, datetime.date(2026, 10, 4)).cget("bg") == "#6366f1"  # 選択中

    def test_weekday_headings_start_on_monday(self, picker):
        picker.open_calendar()
        texts = [label.cget("text") for label in picker._popup._weekday_labels]
        assert texts == ["月", "火", "水", "木", "金", "土", "日"]

    def test_colours_saturday_blue_and_holiday_red(self, picker):
        picker.open_calendar()
        popup = picker._popup
        assert _cell(popup, datetime.date(2026, 10, 3)).cget("fg") == "#2563eb"  # 土曜
        assert _cell(popup, datetime.date(2026, 10, 11)).cget("fg") == "#dc2626"  # 日曜
        assert _cell(popup, datetime.date(2026, 10, 12)).cget("fg") == "#dc2626"  # 登録した祝日
        assert _cell(popup, datetime.date(2026, 10, 5)).cget("fg") == "#0f172a"  # 平日

    def test_days_of_other_months_are_greyed(self, picker):
        picker.open_calendar()
        first = picker._popup._day_labels[0][0]  # 2026-09-28
        assert first._date == datetime.date(2026, 9, 28)
        assert first.cget("fg") == "#94a3b8"

    def test_month_and_year_navigation(self, picker):
        picker.open_calendar()
        popup = picker._popup
        popup._shift_month(1)
        assert (popup._year, popup._month) == (2026, 11)
        popup._shift_month(-2)
        assert (popup._year, popup._month) == (2026, 9)
        popup._shift_year(1)
        assert (popup._year, popup._month) == (2027, 9)
        assert popup._year_label.cget("text") == "2027年"
        assert popup._month_label.cget("text") == "9月"

    def test_picking_a_day_selects_it_calls_back_and_closes(self, picker, calls, app_window):
        picker.open_calendar()
        popup = picker._popup
        cell = _cell(popup, datetime.date(2026, 10, 20))
        popup._on_pick(SimpleNamespace(widget=cell))
        app_window.update()
        assert picker.get_date() == datetime.date(2026, 10, 20)
        assert picker.entry.get() == "2026-10-20"
        assert calls == [1]
        assert not popup.winfo_exists()

    def test_picking_a_day_of_another_month_moves_to_that_date(self, picker):
        picker.open_calendar()
        popup = picker._popup
        popup._on_pick(SimpleNamespace(widget=_cell(popup, datetime.date(2026, 11, 2))))
        assert picker.get_date() == datetime.date(2026, 11, 2)

    def test_escape_closes_the_calendar(self, picker, app_window):
        picker.open_calendar()
        popup = picker._popup
        popup.event_generate("<Escape>")
        app_window.update()
        assert not popup.winfo_exists()

    def test_opening_twice_toggles_it_closed(self, picker, app_window):
        picker.open_calendar()
        popup = picker._popup
        picker.open_calendar()
        app_window.update()
        assert not popup.winfo_exists()

    def test_holidays_are_read_fresh_each_time(self, host, app_window):
        holidays: set[str] = set()
        widget = DatePicker(host, date=datetime.date(2026, 10, 4), holidays=lambda: holidays)
        widget.pack()
        app_window.update()
        widget.open_calendar()
        assert _cell(widget._popup, datetime.date(2026, 10, 14)).cget("fg") == "#0f172a"
        widget._popup.close()
        holidays.add("2026-10-14")  # 設定画面で祝日を追加した場合
        widget.open_calendar()
        assert _cell(widget._popup, datetime.date(2026, 10, 14)).cget("fg") == "#dc2626"
        widget._popup.close()


class TestLanguage:
    def test_english_headings(self, picker):
        i18n.set_language("en")
        try:
            picker.open_calendar()
            popup = picker._popup
            assert popup._month_label.cget("text") == "October"
            assert popup._year_label.cget("text") == "2026"
            assert [w.cget("text") for w in popup._weekday_labels][:2] == ["Mon", "Tue"]
        finally:
            i18n.set_language("ja")
