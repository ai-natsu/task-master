"""ステータス CRUD + 並べ替え（旧 server/src/routes/statuses.ts の移植）。

削除時のガード順序は元実装を踏襲する:
  1. 使用中のタスクが1件以上あれば削除不可
  2. （使用中でなくても）残り1件しかなければ削除不可
"""

import sqlite3

from app.db.connection import generate_id
from app.db.errors import ConflictError, NotFoundError
from app.models import Status


def _row_to_status(row: sqlite3.Row) -> Status:
    return Status(
        id=row["id"],
        label=row["label"],
        color=row["color"],
        order=row["order"],
        is_done=bool(row["isDone"]),
    )


def list_statuses(conn: sqlite3.Connection) -> list[Status]:
    rows = conn.execute('SELECT * FROM "Status" ORDER BY "order" ASC').fetchall()
    return [_row_to_status(r) for r in rows]


def create_status(
    conn: sqlite3.Connection,
    label: str,
    color: str | None = None,
    is_done: bool = False,
) -> Status:
    max_order = conn.execute('SELECT MAX("order") FROM "Status"').fetchone()[0]
    order = (max_order if max_order is not None else -1) + 1
    status_id = generate_id()
    with conn:
        conn.execute(
            """
            INSERT INTO "Status" (id, label, color, "order", isDone)
            VALUES (?, ?, COALESCE(?, '#64748b'), ?, ?)
            """,
            (status_id, label, color, order, 1 if is_done else 0),
        )
    row = conn.execute('SELECT * FROM "Status" WHERE id = ?', (status_id,)).fetchone()
    return _row_to_status(row)


def update_status(
    conn: sqlite3.Connection,
    status_id: str,
    label: str | None = None,
    color: str | None = None,
    is_done: bool | None = None,
) -> Status:
    row = conn.execute('SELECT * FROM "Status" WHERE id = ?', (status_id,)).fetchone()
    if row is None:
        raise NotFoundError("ステータスが見つかりません")
    fields: list[str] = []
    values: list[object] = []
    if label is not None:
        fields.append("label = ?")
        values.append(label)
    if color is not None:
        fields.append("color = ?")
        values.append(color)
    if is_done is not None:
        fields.append("isDone = ?")
        values.append(1 if is_done else 0)
    if fields:
        values.append(status_id)
        with conn:
            conn.execute(f'UPDATE "Status" SET {", ".join(fields)} WHERE id = ?', values)
    row = conn.execute('SELECT * FROM "Status" WHERE id = ?', (status_id,)).fetchone()
    return _row_to_status(row)


def delete_status(conn: sqlite3.Connection, status_id: str) -> None:
    row = conn.execute('SELECT id FROM "Status" WHERE id = ?', (status_id,)).fetchone()
    if row is None:
        raise NotFoundError("ステータスが見つかりません")

    in_use = conn.execute(
        'SELECT COUNT(*) FROM "Task" WHERE status = ?', (status_id,)
    ).fetchone()[0]
    if in_use > 0:
        raise ConflictError(
            f"このステータスは {in_use} 件のタスクで使用中のため削除できません"
        )

    total = conn.execute('SELECT COUNT(*) FROM "Status"').fetchone()[0]
    if total <= 1:
        raise ConflictError("最後のステータスは削除できません")

    with conn:
        conn.execute('DELETE FROM "Status" WHERE id = ?', (status_id,))


def reorder_statuses(conn: sqlite3.Connection, ids: list[str]) -> None:
    with conn:
        for index, status_id in enumerate(ids):
            conn.execute('UPDATE "Status" SET "order" = ? WHERE id = ?', (index, status_id))
