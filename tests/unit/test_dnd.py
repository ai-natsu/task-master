from app.logic.dnd import plan_kanban_drag, plan_tree_drag
from tests.factories import make_task


def _kanban_tasks():
    # TODO列: t1(0), t2(1); DONE列: t3(0)
    return [
        make_task(id="t1", status="TODO", order=0),
        make_task(id="t2", status="TODO", order=1),
        make_task(id="t3", status="DONE", order=0),
    ]


def test_c3_same_column_reorder_only():
    tasks = _kanban_tasks()
    plan = plan_kanban_drag(tasks, "t2", {"id": "t1", "type": "card"})
    assert "status_change" not in plan
    assert plan["reorder"] == [{"id": "t2", "order": 0}, {"id": "t1", "order": 1}]


def test_c4_cross_column_changes_status_and_reindexes_both():
    tasks = _kanban_tasks()
    plan = plan_kanban_drag(tasks, "t1", {"id": "t3", "type": "card"})
    assert plan["status_change"] == {"id": "t1", "status": "DONE"}
    assert plan["reorder"] == [
        {"id": "t1", "order": 0},
        {"id": "t3", "order": 1},
        {"id": "t2", "order": 0},
    ]


def test_c5_drop_on_empty_column_appends_to_end():
    tasks = _kanban_tasks()
    plan = plan_kanban_drag(
        tasks, "t1", {"id": "column:DONE", "type": "column", "status_id": "DONE"}
    )
    assert plan["status_change"] == {"id": "t1", "status": "DONE"}
    t1_entry = next(r for r in plan["reorder"] if r["id"] == "t1")
    assert t1_entry == {"id": "t1", "order": 1}


def test_c6_over_none_is_noop():
    tasks = _kanban_tasks()
    assert plan_kanban_drag(tasks, "t1", None) == {}


def _tree_tasks():
    return [
        make_task(id="a", parent_id=None, order=0),
        make_task(id="b", parent_id=None, order=1),
        make_task(id="c1", parent_id="a", order=0),
    ]


def test_c1_reorders_within_same_parent():
    tasks = _tree_tasks()
    plan = plan_tree_drag(tasks, "b", "a")
    assert plan["reorder"] == [{"id": "b", "order": 0}, {"id": "a", "order": 1}]


def test_c2_cross_parent_drag_is_noop():
    tasks = _tree_tasks()
    assert plan_tree_drag(tasks, "c1", "b") == {}


def test_c2b_dropping_on_itself_is_noop():
    tasks = _tree_tasks()
    assert plan_tree_drag(tasks, "a", "a") == {}
