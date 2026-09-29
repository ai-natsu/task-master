"""タスクのツリー構築（旧 client/src/utils/tree.ts の移植）。"""

from dataclasses import dataclass, field

from app.models import Task


@dataclass
class TaskTreeNode:
    task: Task
    children: list["TaskTreeNode"] = field(default_factory=list)


def build_task_tree(tasks: list[Task]) -> list[TaskTreeNode]:
    node_map: dict[str, TaskTreeNode] = {t.id: TaskTreeNode(task=t) for t in tasks}

    roots: list[TaskTreeNode] = []
    for node in node_map.values():
        parent_id = node.task.parent_id
        if parent_id and parent_id in node_map:
            node_map[parent_id].children.append(node)
        else:
            roots.append(node)

    def sort_rec(nodes: list[TaskTreeNode]) -> None:
        nodes.sort(key=lambda n: n.task.order)
        for n in nodes:
            sort_rec(n.children)

    sort_rec(roots)
    return roots


def count_all(nodes: list[TaskTreeNode]) -> int:
    return sum(1 + count_all(n.children) for n in nodes)


@dataclass
class FlattenedNode:
    node: TaskTreeNode
    depth: int


def flatten_nodes(nodes: list[TaskTreeNode], depth: int = 0) -> list[FlattenedNode]:
    result: list[FlattenedNode] = []
    for n in nodes:
        result.append(FlattenedNode(node=n, depth=depth))
        result.extend(flatten_nodes(n.children, depth + 1))
    return result


@dataclass
class DepthOption:
    id: str
    title: str
    depth: int


def flatten_with_depth(nodes: list[TaskTreeNode], depth: int = 0) -> list[DepthOption]:
    result: list[DepthOption] = []
    for n in nodes:
        result.append(DepthOption(id=n.task.id, title=n.task.title, depth=depth))
        result.extend(flatten_with_depth(n.children, depth + 1))
    return result
