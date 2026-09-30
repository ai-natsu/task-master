import pytest

from app.db.errors import NotFoundError
from app.db.holidays import (
    bulk_upsert_holidays,
    delete_holiday,
    list_holidays,
    parse_holiday_csv,
    upsert_holiday,
)


def test_upsert_creates_new_holiday(conn):
    h = upsert_holiday(conn, "2026-01-01", "元日")
    assert h.date == "2026-01-01"
    assert h.name == "元日"
    assert [x.id for x in list_holidays(conn)] == [h.id]


def test_upsert_same_date_updates_name(conn):
    upsert_holiday(conn, "2026-01-01", "元日")
    updated = upsert_holiday(conn, "2026-01-01", "元日(改名)")
    all_holidays = list_holidays(conn)
    assert len(all_holidays) == 1
    assert all_holidays[0].name == "元日(改名)"
    assert updated.name == "元日(改名)"


def test_list_holidays_ordered_by_date(conn):
    upsert_holiday(conn, "2026-02-11", "建国記念の日")
    upsert_holiday(conn, "2026-01-01", "元日")
    dates = [h.date for h in list_holidays(conn)]
    assert dates == ["2026-01-01", "2026-02-11"]


def test_delete_holiday(conn):
    h = upsert_holiday(conn, "2026-01-01", "元日")
    delete_holiday(conn, h.id)
    assert list_holidays(conn) == []


def test_delete_missing_raises(conn):
    with pytest.raises(NotFoundError):
        delete_holiday(conn, "no-such-id")


def test_parse_csv_iso_dates_with_header():
    raw = "日付,名称\n2026-01-01,元日\n2026-01-12,成人の日\n".encode()
    rows = parse_holiday_csv(raw)
    assert rows == [("2026-01-01", "元日"), ("2026-01-12", "成人の日")]


def test_parse_csv_slash_dates_no_header():
    raw = "2026/1/1,元日\n2026/2/11,建国記念の日\n".encode()
    rows = parse_holiday_csv(raw)
    assert rows == [("2026-01-01", "元日"), ("2026-02-11", "建国記念の日")]


def test_parse_csv_shift_jis_encoding():
    # 文字コード判定(charset-normalizer)は数行程度の短いサンプルだと誤判定しうる
    # ため（実機検証済み）、実利用を想定した複数行のサンプルで検証する。
    holidays = [
        ("2026-01-01", "元日"), ("2026-01-12", "成人の日"), ("2026-02-11", "建国記念の日"),
        ("2026-02-23", "天皇誕生日"), ("2026-03-20", "春分の日"), ("2026-04-29", "昭和の日"),
        ("2026-05-03", "憲法記念日"), ("2026-05-04", "みどりの日"), ("2026-05-05", "こどもの日"),
        ("2026-07-20", "海の日"), ("2026-08-11", "山の日"), ("2026-09-21", "敬老の日"),
        ("2026-09-23", "秋分の日"), ("2026-10-12", "スポーツの日"), ("2026-11-03", "文化の日"),
        ("2026-11-23", "勤労感謝の日"),
    ]
    text = "\r\n".join(f"{d},{n}" for d, n in holidays) + "\r\n"
    raw = text.encode("cp932")
    rows = parse_holiday_csv(raw)
    assert rows == holidays


def test_parse_csv_skips_unparseable_rows():
    raw = "備考,このファイルは自動生成\n2026-01-01,元日\n".encode()
    rows = parse_holiday_csv(raw)
    assert rows == [("2026-01-01", "元日")]


def test_bulk_upsert_inserts_and_updates(conn):
    upsert_holiday(conn, "2026-01-01", "旧名称")
    count = bulk_upsert_holidays(
        conn, [("2026-01-01", "元日"), ("2026-01-12", "成人の日")]
    )
    assert count == 2
    holidays = {h.date: h.name for h in list_holidays(conn)}
    assert holidays == {"2026-01-01": "元日", "2026-01-12": "成人の日"}
