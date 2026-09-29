import datetime

from app.db.projects import create_project, update_project
from app.db.stats import get_stats
from app.db.tasks import create_task, update_task


def _offset(days: float) -> str:
    dt = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=days)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def test_stats_totals_and_breakdowns(conn, statuses):
    p = create_project(conn, "P")
    create_task(conn, title="a", project_id=p.id, status="TODO", priority="HIGH")
    create_task(conn, title="b", project_id=p.id, status="DONE", priority="LOW")

    stats = get_stats(conn, project_id=p.id)
    assert stats["total"] == 2
    assert stats["byStatus"] == {"TODO": 1, "DONE": 1}
    assert stats["byPriority"]["HIGH"] == 1
    assert stats["byPriority"]["LOW"] == 1
    assert stats["completionRate"] == 50.0


def test_completion_rate_zero_when_no_tasks(conn, statuses):
    p = create_project(conn, "P")
    stats = get_stats(conn, project_id=p.id)
    assert stats["total"] == 0
    assert stats["completionRate"] == 0


def test_overdue_excludes_done_tasks(conn, statuses):
    p = create_project(conn, "P")
    create_task(conn, title="overdue-todo", project_id=p.id, status="TODO", due_date=_offset(-1))
    create_task(
        conn, title="overdue-but-done", project_id=p.id, status="DONE", due_date=_offset(-1)
    )

    stats = get_stats(conn, project_id=p.id)
    assert stats["overdue"] == 1


def test_due_soon_window(conn, statuses):
    p = create_project(conn, "P")
    create_task(conn, title="soon", project_id=p.id, status="TODO", due_date=_offset(2))
    create_task(conn, title="far", project_id=p.id, status="TODO", due_date=_offset(10))

    stats = get_stats(conn, project_id=p.id)
    assert stats["dueSoon"] == 1


def test_completed_last_7_days(conn, statuses):
    p = create_project(conn, "P")
    t = create_task(conn, title="done-task", project_id=p.id, status="TODO")
    update_task(conn, t.id, status="DONE")

    stats = get_stats(conn, project_id=p.id)
    assert stats["completedLast7Days"] == 1


def test_global_stats_exclude_archived_projects(conn, statuses):
    visible = create_project(conn, "見える")
    hidden = create_project(conn, "隠れる")
    update_project(conn, hidden.id, archived=True)

    create_task(conn, title="a", project_id=visible.id)
    create_task(conn, title="b", project_id=hidden.id)

    stats = get_stats(conn)
    assert stats["total"] == 1
