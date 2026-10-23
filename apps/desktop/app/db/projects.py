"""プロジェクト CRUD + 並べ替え（旧 server/src/routes/projects.ts の移植）。"""

import sqlite3

from app.db.connection import generate_id, now_iso
from app.db.validation import check_text
from app.models import Project


def _row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        color=row["color"],
        archived=bool(row["archived"]),
        order=row["order"],
        created_at=row["createdAt"],
        updated_at=row["updatedAt"],
        task_count=row["taskCount"] if "taskCount" in row.keys() else 0,
    )


_SELECT_WITH_COUNT = """
    SELECT p.*, (SELECT COUNT(*) FROM "Task" t WHERE t.projectId = p.id) AS taskCount
    FROM "Project" p
"""


def list_projects(conn: sqlite3.Connection, include_archived: bool = False) -> list[Project]:
    where = "" if include_archived else "WHERE p.archived = 0"
    rows = conn.execute(f'{_SELECT_WITH_COUNT} {where} ORDER BY p."order" ASC').fetchall()
    return [_row_to_project(r) for r in rows]


def get_project(conn: sqlite3.Connection, project_id: str) -> Project | None:
    row = conn.execute(f'{_SELECT_WITH_COUNT} WHERE p.id = ?', (project_id,)).fetchone()
    return _row_to_project(row) if row else None


def create_project(
    conn: sqlite3.Connection,
    name: str,
    description: str | None = None,
    color: str | None = None,
) -> Project:
    check_text(name, "名前", "project_name")
    check_text(description, "説明", "project_description", required=False)
    max_order = conn.execute('SELECT MAX("order") FROM "Project"').fetchone()[0]
    order = (max_order if max_order is not None else -1) + 1
    project_id = generate_id()
    ts = now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO "Project"
                (id, name, description, color, archived, "order", createdAt, updatedAt)
            VALUES (?, ?, ?, COALESCE(?, '#6366f1'), 0, ?, ?, ?)
            """,
            (project_id, name, description, color, order, ts, ts),
        )
    return get_project(conn, project_id)  # type: ignore[return-value]


def update_project(
    conn: sqlite3.Connection,
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
    archived: bool | None = None,
) -> Project | None:
    check_text(name, "名前", "project_name")
    check_text(description, "説明", "project_description", required=False)
    if get_project(conn, project_id) is None:
        return None
    fields: list[str] = []
    values: list[object] = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if color is not None:
        fields.append("color = ?")
        values.append(color)
    if archived is not None:
        fields.append("archived = ?")
        values.append(1 if archived else 0)
    fields.append("updatedAt = ?")
    values.append(now_iso())
    values.append(project_id)
    with conn:
        conn.execute(f'UPDATE "Project" SET {", ".join(fields)} WHERE id = ?', values)
    return get_project(conn, project_id)


def delete_project(conn: sqlite3.Connection, project_id: str) -> bool:
    if get_project(conn, project_id) is None:
        return False
    with conn:
        conn.execute('DELETE FROM "Project" WHERE id = ?', (project_id,))
    return True


def reorder_projects(conn: sqlite3.Connection, ids: list[str]) -> None:
    with conn:
        for index, project_id in enumerate(ids):
            conn.execute('UPDATE "Project" SET "order" = ? WHERE id = ?', (index, project_id))
