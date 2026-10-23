import pytest

from app.db.errors import ConflictError, NotFoundError
from app.db.projects import create_project
from app.db.statuses import (
    create_status,
    delete_status,
    list_statuses,
    reorder_statuses,
    update_status,
)
from app.db.tasks import create_task


def test_create_status_order_increments(conn):
    s1 = create_status(conn, "未着手")
    s2 = create_status(conn, "完了", is_done=True)
    assert s2.order == s1.order + 1
    assert s1.is_done is False
    assert s2.is_done is True


def test_update_status_partial(conn):
    s = create_status(conn, "元のラベル", color="#000000")
    updated = update_status(conn, s.id, label="新しいラベル")
    assert updated.label == "新しいラベル"
    assert updated.color == "#000000"


def test_update_missing_raises(conn):
    with pytest.raises(NotFoundError):
        update_status(conn, "no-such-id", label="x")


def test_delete_blocked_when_in_use(conn):
    s = create_status(conn, "使用中")
    p = create_project(conn, "P")
    create_task(conn, title="T", project_id=p.id, status=s.id)

    with pytest.raises(ConflictError, match="1 件のタスクで使用中"):
        delete_status(conn, s.id)


def test_delete_blocked_when_last_remaining(conn):
    s = create_status(conn, "唯一のステータス")
    with pytest.raises(ConflictError, match="最後のステータスは削除できません"):
        delete_status(conn, s.id)


def test_delete_succeeds_when_unused_and_not_last(conn):
    s1 = create_status(conn, "A")
    s2 = create_status(conn, "B")
    delete_status(conn, s2.id)
    assert [s.id for s in list_statuses(conn)] == [s1.id]


def test_reorder_statuses(conn):
    s1 = create_status(conn, "A")
    s2 = create_status(conn, "B")
    s3 = create_status(conn, "C")
    reorder_statuses(conn, [s3.id, s1.id, s2.id])
    assert [s.id for s in list_statuses(conn)] == [s3.id, s1.id, s2.id]
