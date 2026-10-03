"""タスク CRUD + 並べ替え + 移動（旧 server/src/routes/tasks.ts の移植）。"""

import sqlite3

from app.db.connection import generate_id, now_iso
from app.db.errors import CycleError, NotFoundError, ValidationError
from app.models import Tag, Task

_UNSET = object()


def _row_to_task(conn: sqlite3.Connection, row: sqlite3.Row) -> Task:
    tag_rows = conn.execute(
        """
        SELECT t.id, t.name, t.color
        FROM "TaskTag" tt
        JOIN "Tag" t ON t.id = tt.tagId
        WHERE tt.taskId = ?
        ORDER BY t.name ASC
        """,
        (row["id"],),
    ).fetchall()
    tags = [Tag(id=r["id"], name=r["name"], color=r["color"]) for r in tag_rows]
    return Task(
        id=row["id"],
        title=row["title"],
        project_id=row["projectId"],
        description=row["description"],
        status=row["status"],
        priority=row["priority"],
        start_date=row["startDate"],
        due_date=row["dueDate"],
        order=row["order"],
        created_at=row["createdAt"],
        updated_at=row["updatedAt"],
        parent_id=row["parentId"],
        tags=tags,
    )


def get_task(conn: sqlite3.Connection, task_id: str) -> Task | None:
    row = conn.execute('SELECT * FROM "Task" WHERE id = ?', (task_id,)).fetchone()
    return _row_to_task(conn, row) if row else None


def is_descendant_or_self(
    conn: sqlite3.Connection, task_id: str, candidate_ancestor_id: str
) -> bool:
    if task_id == candidate_ancestor_id:
        return True
    children = conn.execute('SELECT id FROM "Task" WHERE parentId = ?', (task_id,)).fetchall()
    return any(
        is_descendant_or_self(conn, child["id"], candidate_ancestor_id) for child in children
    )


def list_tasks(
    conn: sqlite3.Connection,
    project_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    tag_id: str | None = None,
    search: str | None = None,
    parent_id: object = _UNSET,
) -> list[Task]:
    where = []
    params: list[object] = []

    if project_id:
        where.append("t.projectId = ?")
        params.append(project_id)
    else:
        where.append('t.projectId IN (SELECT id FROM "Project" WHERE archived = 0)')

    if status:
        where.append("t.status = ?")
        params.append(status)
    if priority:
        where.append("t.priority = ?")
        params.append(priority)

    if parent_id is not _UNSET:
        if parent_id is None:
            where.append("t.parentId IS NULL")
        else:
            where.append("t.parentId = ?")
            params.append(parent_id)

    if search:
        where.append("(t.title LIKE ? OR t.description LIKE ?)")
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    if tag_id:
        where.append('t.id IN (SELECT taskId FROM "TaskTag" WHERE tagId = ?)')
        params.append(tag_id)

    sql = (
        f'SELECT t.* FROM "Task" t WHERE {" AND ".join(where)} '
        'ORDER BY t."order" ASC, t.createdAt ASC'
    )
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(conn, r) for r in rows]


def create_task(
    conn: sqlite3.Connection,
    title: str,
    project_id: str,
    description: str | None = None,
    parent_id: str | None = None,
    status: str | None = None,
    priority: str = "MEDIUM",
    start_date: str | None = None,
    due_date: str | None = None,
    tag_ids: list[str] | None = None,
) -> Task:
    if parent_id is not None:
        parent = conn.execute('SELECT id FROM "Task" WHERE id = ?', (parent_id,)).fetchone()
        if parent is None:
            raise ValidationError("親タスクが見つかりません")

    if status is not None:
        status_row = conn.execute('SELECT id FROM "Status" WHERE id = ?', (status,)).fetchone()
        if status_row is None:
            raise ValidationError("指定のステータスが存在しません")
    else:
        first_status = conn.execute(
            'SELECT id FROM "Status" ORDER BY "order" ASC LIMIT 1'
        ).fetchone()
        if first_status is None:
            raise ValidationError("ステータスが1件もありません")
        status = first_status["id"]

    max_order = conn.execute(
        'SELECT MAX("order") FROM "Task" WHERE projectId = ? AND parentId IS ?',
        (project_id, parent_id),
    ).fetchone()[0]
    order = (max_order if max_order is not None else -1) + 1

    task_id = generate_id()
    ts = now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO "Task"
                (id, title, description, status, priority, startDate, dueDate,
                 "order", createdAt, updatedAt, projectId, parentId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id, title, description, status, priority, start_date, due_date,
                order, ts, ts, project_id, parent_id,
            ),
        )
        if tag_ids:
            conn.executemany(
                'INSERT INTO "TaskTag" (taskId, tagId) VALUES (?, ?)',
                [(task_id, tag_id) for tag_id in tag_ids],
            )
    return get_task(conn, task_id)  # type: ignore[return-value]


def update_task(
    conn: sqlite3.Connection,
    task_id: str,
    title: str | None = None,
    description: object = _UNSET,
    status: str | None = None,
    priority: str | None = None,
    start_date: object = _UNSET,
    due_date: object = _UNSET,
    tag_ids: list[str] | None = None,
) -> Task:
    if get_task(conn, task_id) is None:
        raise NotFoundError("タスクが見つかりません")

    if status is not None:
        status_row = conn.execute('SELECT id FROM "Status" WHERE id = ?', (status,)).fetchone()
        if status_row is None:
            raise ValidationError("指定のステータスが存在しません")

    fields: list[str] = []
    values: list[object] = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if description is not _UNSET:
        fields.append("description = ?")
        values.append(description)
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if priority is not None:
        fields.append("priority = ?")
        values.append(priority)
    if start_date is not _UNSET:
        fields.append("startDate = ?")
        values.append(start_date)
    if due_date is not _UNSET:
        fields.append("dueDate = ?")
        values.append(due_date)
    fields.append("updatedAt = ?")
    values.append(now_iso())
    values.append(task_id)

    with conn:
        conn.execute(f'UPDATE "Task" SET {", ".join(fields)} WHERE id = ?', values)
        if tag_ids is not None:
            conn.execute('DELETE FROM "TaskTag" WHERE taskId = ?', (task_id,))
            if tag_ids:
                conn.executemany(
                    'INSERT INTO "TaskTag" (taskId, tagId) VALUES (?, ?)',
                    [(task_id, tag_id) for tag_id in tag_ids],
                )
    return get_task(conn, task_id)  # type: ignore[return-value]


def move_task(
    conn: sqlite3.Connection,
    task_id: str,
    parent_id: object = _UNSET,
    project_id: object = _UNSET,
    order: object = _UNSET,
) -> Task:
    if get_task(conn, task_id) is None:
        raise NotFoundError("タスクが見つかりません")

    if parent_id is not _UNSET and parent_id:
        if is_descendant_or_self(conn, task_id, parent_id):
            raise CycleError("タスクを自分自身またはその配下には移動できません")

    fields: list[str] = []
    values: list[object] = []
    if parent_id is not _UNSET:
        fields.append("parentId = ?")
        values.append(parent_id)
    if project_id is not _UNSET:
        fields.append("projectId = ?")
        values.append(project_id)
    if order is not _UNSET:
        fields.append('"order" = ?')
        values.append(order)
    if fields:
        values.append(task_id)
        with conn:
            conn.execute(f'UPDATE "Task" SET {", ".join(fields)} WHERE id = ?', values)
    return get_task(conn, task_id)  # type: ignore[return-value]


def reorder_tasks(conn: sqlite3.Connection, items: list[dict]) -> None:
    with conn:
        for item in items:
            fields = ['"order" = ?']
            values: list[object] = [item["order"]]
            if "parent_id" in item:
                fields.append("parentId = ?")
                values.append(item["parent_id"])
            if "project_id" in item:
                fields.append("projectId = ?")
                values.append(item["project_id"])
            values.append(item["id"])
            conn.execute(f'UPDATE "Task" SET {", ".join(fields)} WHERE id = ?', values)


def delete_task(conn: sqlite3.Connection, task_id: str) -> None:
    if get_task(conn, task_id) is None:
        raise NotFoundError("タスクが見つかりません")
    with conn:
        conn.execute('DELETE FROM "Task" WHERE id = ?', (task_id,))
