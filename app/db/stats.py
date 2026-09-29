"""統計集計（旧 server/src/routes/stats.ts の移植）。

「完了」の判定は常に Status.isDone を動的に参照する（"DONE" 文字列のハード
コード禁止、という元実装の方針を踏襲）。
"""

import datetime
import sqlite3

from app.constants import PRIORITIES
from app.db.statuses import list_statuses


def _iso(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def get_stats(conn: sqlite3.Connection, project_id: str | None = None) -> dict:
    if project_id:
        where = "projectId = ?"
        params: list[object] = [project_id]
    else:
        where = 'projectId IN (SELECT id FROM "Project" WHERE archived = 0)'
        params = []

    statuses = list_statuses(conn)
    done_ids = [s.id for s in statuses if s.is_done]

    total = conn.execute(f'SELECT COUNT(*) FROM "Task" WHERE {where}', params).fetchone()[0]

    by_status = {s.id: 0 for s in statuses}
    for row in conn.execute(
        f'SELECT status, COUNT(*) AS c FROM "Task" WHERE {where} GROUP BY status', params
    ):
        by_status[row["status"]] = row["c"]

    by_priority = {p: 0 for p in PRIORITIES}
    for row in conn.execute(
        f'SELECT priority, COUNT(*) AS c FROM "Task" WHERE {where} GROUP BY priority', params
    ):
        by_priority[row["priority"]] = row["c"]

    now = datetime.datetime.now(datetime.UTC)
    now_iso = _iso(now)
    soon_iso = _iso(now + datetime.timedelta(days=3))
    week_ago_iso = _iso(now - datetime.timedelta(days=7))

    done_placeholders = ",".join("?" for _ in done_ids) if done_ids else "NULL"

    overdue = conn.execute(
        f'SELECT COUNT(*) FROM "Task" WHERE {where} AND status NOT IN ({done_placeholders}) '
        f"AND dueDate IS NOT NULL AND dueDate < ?",
        [*params, *done_ids, now_iso],
    ).fetchone()[0]

    due_soon = conn.execute(
        f'SELECT COUNT(*) FROM "Task" WHERE {where} AND status NOT IN ({done_placeholders}) '
        f"AND dueDate IS NOT NULL AND dueDate >= ? AND dueDate <= ?",
        [*params, *done_ids, now_iso, soon_iso],
    ).fetchone()[0]

    completed_last_7_days = conn.execute(
        f'SELECT COUNT(*) FROM "Task" WHERE {where} AND status IN ({done_placeholders}) '
        f"AND updatedAt >= ?",
        [*params, *done_ids, week_ago_iso],
    ).fetchone()[0]

    done = sum(by_status[i] for i in done_ids)
    completion_rate = round((done / total) * 1000) / 10 if total > 0 else 0

    return {
        "total": total,
        "byStatus": by_status,
        "byPriority": by_priority,
        "overdue": overdue,
        "dueSoon": due_soon,
        "completedLast7Days": completed_last_7_days,
        "completionRate": completion_rate,
    }
