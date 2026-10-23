"""祝日 CRUD + CSV一括登録。

祝日は「設定」画面でユーザーが管理する。ガントチャートの休日色分けにも
将来利用する想定（現時点では未接続）。
"""

import csv
import datetime
import io
import sqlite3

from charset_normalizer import from_bytes as detect_charset

from app.db.connection import generate_id
from app.db.errors import NotFoundError, ValidationError
from app.db.validation import check_text
from app.models import Holiday


def _row_to_holiday(row: sqlite3.Row) -> Holiday:
    return Holiday(id=row["id"], date=row["date"], name=row["name"])


def list_holidays(conn: sqlite3.Connection) -> list[Holiday]:
    rows = conn.execute('SELECT * FROM "Holiday" ORDER BY date ASC').fetchall()
    return [_row_to_holiday(r) for r in rows]


def upsert_holiday(conn: sqlite3.Connection, date: str, name: str) -> Holiday:
    """日付が一致する行があれば名称を更新、無ければ新規作成する。"""
    check_text(name, "名称", "holiday_name")
    with conn:
        conn.execute(
            """
            INSERT INTO "Holiday" (id, date, name) VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET name = excluded.name
            """,
            (generate_id(), date, name),
        )
    row = conn.execute('SELECT * FROM "Holiday" WHERE date = ?', (date,)).fetchone()
    return _row_to_holiday(row)


def delete_holiday(conn: sqlite3.Connection, holiday_id: str) -> None:
    row = conn.execute('SELECT id FROM "Holiday" WHERE id = ?', (holiday_id,)).fetchone()
    if row is None:
        raise NotFoundError("祝日が見つかりません")
    with conn:
        conn.execute('DELETE FROM "Holiday" WHERE id = ?', (holiday_id,))


def _parse_date(text: str) -> str | None:
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def parse_holiday_csv(raw_bytes: bytes) -> list[tuple[str, str]]:
    """CSVバイト列を (date, name) のリストへ変換する。

    列順は「日付, 名称」固定。日付が解釈できない先頭行はヘッダーとして
    読み飛ばす。文字コードはcharset-normalizerの判定結果をそのまま使う
    （UTF-8/Shift-JISの決め打ち判定はしない）。ごく短いファイルでは
    誤判定の可能性がある（実機検証済み、詳細はコミットメッセージ参照）。
    """
    detected = detect_charset(raw_bytes).best()
    if detected is None:
        raise ValidationError("CSVの文字コードを判定できませんでした")
    text = str(detected)

    rows: list[tuple[str, str]] = []
    # newline='' が無いと、旧Mac式の"\r"のみの改行を含むファイルで
    # 「new-line character seen in unquoted field」エラーになる（実機検証済み）。
    # \n・\r\n は newline 指定の有無に関わらずcsvモジュールが正しく解釈する。
    for cells in csv.reader(io.StringIO(text, newline="")):
        if len(cells) < 2:
            continue
        date = _parse_date(cells[0])
        name = cells[1].strip()
        if date is None or not name:
            continue  # ヘッダー行や空行はここで自然に読み飛ばされる
        rows.append((date, name))
    return rows


def bulk_upsert_holidays(conn: sqlite3.Connection, rows: list[tuple[str, str]]) -> int:
    for _date, name in rows:
        check_text(name, "名称", "holiday_name")
    with conn:
        conn.executemany(
            """
            INSERT INTO "Holiday" (id, date, name) VALUES (:id, :date, :name)
            ON CONFLICT(date) DO UPDATE SET name = excluded.name
            """,
            [{"id": generate_id(), "date": date, "name": name} for date, name in rows],
        )
    return len(rows)
