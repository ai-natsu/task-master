from app.db.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    reorder_projects,
    update_project,
)
from app.db.tasks import create_task


def test_create_project_defaults(conn):
    p = create_project(conn, "プロジェクトA")
    assert p.color == "#6366f1"
    assert p.archived is False
    assert p.order == 0


def test_order_increments(conn):
    p1 = create_project(conn, "A")
    p2 = create_project(conn, "B")
    assert p2.order == p1.order + 1


def test_list_excludes_archived_by_default(conn):
    p1 = create_project(conn, "見える")
    p2 = create_project(conn, "隠れる")
    update_project(conn, p2.id, archived=True)

    visible = list_projects(conn)
    assert [p.id for p in visible] == [p1.id]

    all_projects = list_projects(conn, include_archived=True)
    assert {p.id for p in all_projects} == {p1.id, p2.id}


def test_update_partial_fields_only(conn):
    p = create_project(conn, "元の名前", description="元の説明")
    updated = update_project(conn, p.id, name="新しい名前")
    assert updated.name == "新しい名前"
    assert updated.description == "元の説明"


def test_delete_cascades_tasks(conn, statuses):
    p = create_project(conn, "削除対象")
    create_task(conn, title="タスク", project_id=p.id)

    assert delete_project(conn, p.id) is True
    assert get_project(conn, p.id) is None
    remaining = conn.execute(
        'SELECT COUNT(*) FROM "Task" WHERE projectId = ?', (p.id,)
    ).fetchone()[0]
    assert remaining == 0


def test_delete_missing_returns_false(conn):
    assert delete_project(conn, "no-such-id") is False


def test_reorder_projects(conn):
    p1 = create_project(conn, "A")
    p2 = create_project(conn, "B")
    p3 = create_project(conn, "C")

    reorder_projects(conn, [p3.id, p1.id, p2.id])

    ordered = list_projects(conn)
    assert [p.id for p in ordered] == [p3.id, p1.id, p2.id]
