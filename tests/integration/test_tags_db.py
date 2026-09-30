import pytest

from app.db.errors import ConflictError, NotFoundError
from app.db.projects import create_project
from app.db.tags import count_tagged_tasks, create_tag, delete_tag, list_tags, update_tag
from app.db.tasks import create_task, get_task


def test_create_and_list_tags_ordered_by_name(conn):
    create_tag(conn, "urgent", "#ef4444")
    create_tag(conn, "backend", "#0ea5e9")
    names = [t.name for t in list_tags(conn)]
    assert names == ["backend", "urgent"]


def test_duplicate_name_raises_conflict(conn):
    create_tag(conn, "urgent")
    with pytest.raises(ConflictError):
        create_tag(conn, "urgent")


def test_delete_missing_raises_not_found(conn):
    with pytest.raises(NotFoundError):
        delete_tag(conn, "no-such-id")


def test_delete_tag_removes_task_association(conn, statuses):
    tag = create_tag(conn, "design")
    p = create_project(conn, "P")
    task = create_task(conn, title="T", project_id=p.id, tag_ids=[tag.id])
    assert [t.id for t in get_task(conn, task.id).tags] == [tag.id]

    delete_tag(conn, tag.id)

    assert get_task(conn, task.id).tags == []


def test_update_tag_renames_and_recolors(conn):
    tag = create_tag(conn, "urgent", "#ef4444")
    updated = update_tag(conn, tag.id, name="hot", color="#f97316")
    assert updated.name == "hot"
    assert updated.color == "#f97316"


def test_update_tag_missing_raises_not_found(conn):
    with pytest.raises(NotFoundError):
        update_tag(conn, "no-such-id", name="x")


def test_update_tag_duplicate_name_raises_conflict(conn):
    create_tag(conn, "urgent")
    other = create_tag(conn, "backend")
    with pytest.raises(ConflictError):
        update_tag(conn, other.id, name="urgent")


def test_count_tagged_tasks(conn, statuses):
    tag = create_tag(conn, "design")
    p = create_project(conn, "P")
    assert count_tagged_tasks(conn, tag.id) == 0

    create_task(conn, title="T1", project_id=p.id, tag_ids=[tag.id])
    create_task(conn, title="T2", project_id=p.id, tag_ids=[tag.id])
    assert count_tagged_tasks(conn, tag.id) == 2
