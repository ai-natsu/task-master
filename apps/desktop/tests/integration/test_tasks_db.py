import pytest

from app.db.errors import CycleError, NotFoundError, ValidationError
from app.db.projects import create_project, update_project
from app.db.tags import create_tag
from app.db.tasks import (
    create_task,
    delete_task,
    get_task,
    is_descendant_or_self,
    list_tasks,
    move_task,
    reorder_tasks,
    update_task,
)


def test_create_without_statuses_raises(conn):
    p = create_project(conn, "P")
    with pytest.raises(ValidationError, match="ステータスが1件もありません"):
        create_task(conn, title="T", project_id=p.id)


def test_create_auto_picks_lowest_order_status(conn, statuses):
    p = create_project(conn, "P")
    t = create_task(conn, title="T", project_id=p.id)
    assert t.status == "TODO"


def test_create_with_invalid_status_raises(conn, statuses):
    p = create_project(conn, "P")
    with pytest.raises(ValidationError, match="指定のステータスが存在しません"):
        create_task(conn, title="T", project_id=p.id, status="NOPE")


def test_create_with_missing_parent_raises(conn, statuses):
    p = create_project(conn, "P")
    with pytest.raises(ValidationError, match="親タスクが見つかりません"):
        create_task(conn, title="T", project_id=p.id, parent_id="no-such-id")


def test_sibling_order_increments_independently_per_parent(conn, statuses):
    p = create_project(conn, "P")
    root1 = create_task(conn, title="root1", project_id=p.id)
    root2 = create_task(conn, title="root2", project_id=p.id)
    assert root2.order == root1.order + 1

    child1 = create_task(conn, title="child1", project_id=p.id, parent_id=root1.id)
    child2 = create_task(conn, title="child2", project_id=p.id, parent_id=root1.id)
    assert child1.order == 0
    assert child2.order == 1


def test_update_tag_ids_replaces_not_merges(conn, statuses):
    p = create_project(conn, "P")
    tag_a = create_tag(conn, "a")
    tag_b = create_tag(conn, "b")
    t = create_task(conn, title="T", project_id=p.id, tag_ids=[tag_a.id])

    updated = update_task(conn, t.id, tag_ids=[tag_b.id])
    assert [tag.id for tag in updated.tags] == [tag_b.id]


def test_update_missing_raises(conn):
    with pytest.raises(NotFoundError):
        update_task(conn, "no-such-id", title="x")


def test_is_descendant_or_self(conn, statuses):
    p = create_project(conn, "P")
    root = create_task(conn, title="root", project_id=p.id)
    child = create_task(conn, title="child", project_id=p.id, parent_id=root.id)
    grandchild = create_task(conn, title="grandchild", project_id=p.id, parent_id=child.id)
    other = create_task(conn, title="other", project_id=p.id)

    assert is_descendant_or_self(conn, root.id, root.id) is True
    assert is_descendant_or_self(conn, root.id, grandchild.id) is True
    assert is_descendant_or_self(conn, root.id, other.id) is False


def test_move_task_rejects_cycle_onto_self(conn, statuses):
    p = create_project(conn, "P")
    root = create_task(conn, title="root", project_id=p.id)
    with pytest.raises(CycleError):
        move_task(conn, root.id, parent_id=root.id)


def test_move_task_rejects_cycle_onto_descendant(conn, statuses):
    p = create_project(conn, "P")
    root = create_task(conn, title="root", project_id=p.id)
    child = create_task(conn, title="child", project_id=p.id, parent_id=root.id)
    with pytest.raises(CycleError):
        move_task(conn, root.id, parent_id=child.id)


def test_move_task_allows_valid_reparent(conn, statuses):
    p = create_project(conn, "P")
    a = create_task(conn, title="a", project_id=p.id)
    b = create_task(conn, title="b", project_id=p.id)
    moved = move_task(conn, b.id, parent_id=a.id)
    assert moved.parent_id == a.id


def test_list_filters_by_parent_id_null_returns_roots_only(conn, statuses):
    p = create_project(conn, "P")
    root = create_task(conn, title="root", project_id=p.id)
    create_task(conn, title="child", project_id=p.id, parent_id=root.id)

    roots = list_tasks(conn, project_id=p.id, parent_id=None)
    assert [t.id for t in roots] == [root.id]


def test_list_excludes_tasks_of_archived_project_when_no_project_filter(conn, statuses):
    visible_p = create_project(conn, "見える")
    hidden_p = create_project(conn, "隠れる")
    update_project(conn, hidden_p.id, archived=True)

    visible_task = create_task(conn, title="見えるタスク", project_id=visible_p.id)
    create_task(conn, title="隠れるタスク", project_id=hidden_p.id)

    results = list_tasks(conn)
    assert [t.id for t in results] == [visible_task.id]


def test_list_filters_by_search(conn, statuses):
    p = create_project(conn, "P")
    match = create_task(conn, title="ログイン機能の実装", project_id=p.id)
    create_task(conn, title="別のタスク", project_id=p.id)

    results = list_tasks(conn, project_id=p.id, search="ログイン")
    assert [t.id for t in results] == [match.id]


def test_reorder_tasks_can_change_parent(conn, statuses):
    p = create_project(conn, "P")
    a = create_task(conn, title="a", project_id=p.id)
    b = create_task(conn, title="b", project_id=p.id)

    reorder_tasks(conn, [{"id": b.id, "order": 0, "parent_id": a.id}])

    assert get_task(conn, b.id).parent_id == a.id


def test_delete_missing_raises(conn):
    with pytest.raises(NotFoundError):
        delete_task(conn, "no-such-id")


def test_delete_cascades_subtasks_and_tags(conn, statuses):
    p = create_project(conn, "P")
    tag = create_tag(conn, "t")
    root = create_task(conn, title="root", project_id=p.id, tag_ids=[tag.id])
    child = create_task(conn, title="child", project_id=p.id, parent_id=root.id)

    delete_task(conn, root.id)

    assert get_task(conn, root.id) is None
    assert get_task(conn, child.id) is None
    tag_links = conn.execute(
        'SELECT COUNT(*) FROM "TaskTag" WHERE taskId = ?', (root.id,)
    ).fetchone()[0]
    assert tag_links == 0
