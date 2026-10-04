"""タグ CRUD（旧 server/src/routes/tags.ts の移植）。"""

import sqlite3

from app.db.connection import generate_id
from app.db.errors import ConflictError, NotFoundError
from app.db.validation import check_text
from app.models import Tag


def _row_to_tag(row: sqlite3.Row) -> Tag:
    return Tag(id=row["id"], name=row["name"], color=row["color"])


def list_tags(conn: sqlite3.Connection) -> list[Tag]:
    rows = conn.execute('SELECT * FROM "Tag" ORDER BY name ASC').fetchall()
    return [_row_to_tag(r) for r in rows]


def create_tag(conn: sqlite3.Connection, name: str, color: str | None = None) -> Tag:
    check_text(name, "名前", "tag_name")
    tag_id = generate_id()
    try:
        with conn:
            conn.execute(
                'INSERT INTO "Tag" (id, name, color) VALUES (?, ?, COALESCE(?, \'#94a3b8\'))',
                (tag_id, name, color),
            )
    except sqlite3.IntegrityError as exc:
        raise ConflictError("タグが既に存在します") from exc
    row = conn.execute('SELECT * FROM "Tag" WHERE id = ?', (tag_id,)).fetchone()
    return _row_to_tag(row)


def update_tag(
    conn: sqlite3.Connection, tag_id: str, name: str | None = None, color: str | None = None
) -> Tag:
    check_text(name, "名前", "tag_name")
    row = conn.execute('SELECT * FROM "Tag" WHERE id = ?', (tag_id,)).fetchone()
    if row is None:
        raise NotFoundError("タグが見つかりません")
    fields: list[str] = []
    values: list[object] = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if color is not None:
        fields.append("color = ?")
        values.append(color)
    if fields:
        values.append(tag_id)
        try:
            with conn:
                conn.execute(f'UPDATE "Tag" SET {", ".join(fields)} WHERE id = ?', values)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("タグが既に存在します") from exc
    row = conn.execute('SELECT * FROM "Tag" WHERE id = ?', (tag_id,)).fetchone()
    return _row_to_tag(row)


def delete_tag(conn: sqlite3.Connection, tag_id: str) -> None:
    row = conn.execute('SELECT id FROM "Tag" WHERE id = ?', (tag_id,)).fetchone()
    if row is None:
        raise NotFoundError("タグが見つかりません")
    with conn:
        conn.execute('DELETE FROM "Tag" WHERE id = ?', (tag_id,))


def count_tagged_tasks(conn: sqlite3.Connection, tag_id: str) -> int:
    """このタグが付いているタスク数（削除確認ダイアログでの影響件数表示用）。"""
    return conn.execute(
        'SELECT COUNT(*) FROM "TaskTag" WHERE tagId = ?', (tag_id,)
    ).fetchone()[0]
