from app.logic.dnd import plan_kanban_drag, plan_row_drop, plan_tree_drag
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


def _row_tasks():
    # ルート: a(0), b(1)。a の子: a1(0), a2(1)。b の子: b1(0)
    return [
        make_task(id="a", parent_id=None, order=0),
        make_task(id="b", parent_id=None, order=1),
        make_task(id="a1", parent_id="a", order=0),
        make_task(id="a2", parent_id="a", order=1),
        make_task(id="b1", parent_id="b", order=0),
    ]


def test_row_drop_before_sibling_same_parent_reorders_only():
    plan = plan_row_drop(_row_tasks(), "a2", "a1", "before")
    assert plan["reorder"] == [{"id": "a2", "order": 0}, {"id": "a1", "order": 1}]


def test_row_drop_no_change_returns_empty():
    assert plan_row_drop(_row_tasks(), "a1", "a2", "before") == {}
    assert plan_row_drop(_row_tasks(), "a1", "a1", "child") == {}


def test_row_drop_child_makes_it_the_last_child_of_another_parent():
    plan = plan_row_drop(_row_tasks(), "a1", "b", "child")
    assert plan["reorder"] == [
        {"id": "b1", "order": 0},
        {"id": "a1", "order": 1, "parent_id": "b"},
        {"id": "a2", "order": 0},  # 元の親の兄弟を詰め直す
    ]


def test_row_drop_before_top_level_row_promotes_child_to_top_level():
    plan = plan_row_drop(_row_tasks(), "a1", "b", "before")
    assert plan["reorder"] == [
        {"id": "a", "order": 0},
        {"id": "a1", "order": 1, "parent_id": None},
        {"id": "b", "order": 2},
        {"id": "a2", "order": 0},
    ]


def test_row_drop_after_places_below_target_under_target_parent():
    plan = plan_row_drop(_row_tasks(), "a1", "b1", "after")
    assert plan["reorder"][:2] == [
        {"id": "b1", "order": 0},
        {"id": "a1", "order": 1, "parent_id": "b"},
    ]


def test_row_drop_rejects_cycle_into_own_subtree():
    assert plan_row_drop(_row_tasks(), "a", "a1", "child") == {}
    assert plan_row_drop(_row_tasks(), "a", "a2", "after") == {}


def test_row_drop_rejects_unknown_zone_and_ids():
    assert plan_row_drop(_row_tasks(), "a1", "b", "middle") == {}
    assert plan_row_drop(_row_tasks(), "zzz", "b", "child") == {}
