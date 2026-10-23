from app.logic.tree import (
    build_task_tree,
    count_all,
    flatten_nodes,
    flatten_with_depth,
)
from tests.factories import make_task


def test_u1_nests_children_sorted_by_order():
    tasks = [
        make_task(id="a", order=1),
        make_task(id="b", order=0),
        make_task(id="a1", parent_id="a", order=1),
        make_task(id="a0", parent_id="a", order=0),
    ]
    tree = build_task_tree(tasks)
    assert [n.task.id for n in tree] == ["b", "a"]
    a = next(n for n in tree if n.task.id == "a")
    assert [c.task.id for c in a.children] == ["a0", "a1"]


def test_u2_orphan_parent_becomes_root():
    tasks = [make_task(id="orphan", parent_id="gone")]
    tree = build_task_tree(tasks)
    assert [n.task.id for n in tree] == ["orphan"]


def test_u3_empty_input_yields_empty_tree():
    assert build_task_tree([]) == []


def _sample_tree():
    tasks = [
        make_task(id="a", order=0),
        make_task(id="a0", parent_id="a", order=0),
        make_task(id="a0x", parent_id="a0", order=0),
        make_task(id="b", order=1),
    ]
    return build_task_tree(tasks)


def test_u4_flatten_with_depth_dfs_order():
    tree = _sample_tree()
    result = [(o.id, o.depth) for o in flatten_with_depth(tree)]
    assert result == [("a", 0), ("a0", 1), ("a0x", 2), ("b", 0)]


def test_u5_flatten_nodes_parent_before_child():
    tree = _sample_tree()
    result = [(f.node.task.id, f.depth) for f in flatten_nodes(tree)]
    assert result == [("a", 0), ("a0", 1), ("a0x", 2), ("b", 0)]


def test_u6_count_all_counts_every_descendant():
    tree = _sample_tree()
    assert count_all(tree) == 4
