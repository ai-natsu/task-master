"""カンバン/ツリーのドラッグ&ドロップ計画（旧 client/src/utils/dnd.ts の移植）。

戻り値はそのまま app.db.tasks.update_task / reorder_tasks に渡せる
{"id":.., "order":..} 辞書のリストとする。
"""

from app.models import Task


def _array_move(items: list, from_index: int, to_index: int) -> list:
    """@dnd-kit/sortable の arrayMove と同じ意味論（負の to_index にも対応）。"""
    new_list = list(items)
    length = len(new_list)
    insert_at = length + to_index if to_index < 0 else to_index
    item = new_list.pop(from_index)
    new_list.insert(insert_at, item)
    return new_list


def plan_kanban_drag(tasks: list[Task], active_id: str, over: dict | None) -> dict:
    """カンバンドラッグの純粋な意思決定ロジック。

    戻り値:
      - "status_change": 別の列に移動した場合のみ設定
      - "reorder": 永続化すべき新しい {id, order} リスト（無ければ no-op）
    """
    if not over:
        return {}

    task = next((t for t in tasks if t.id == active_id), None)
    if task is None:
        return {}

    columns: dict[str, list[Task]] = {}
    for t in tasks:
        columns.setdefault(t.status, []).append(t)
    for col in columns.values():
        col.sort(key=lambda t: t.order)

    if over["type"] == "card":
        over_task = next((t for t in tasks if t.id == over["id"]), None)
        if over_task is None:
            return {}
        target_status = over_task.status
        target_col = columns.get(target_status, [])
        target_index = next((i for i, t in enumerate(target_col) if t.id == over_task.id), 0)
    else:
        target_status = over["status_id"]
        target_index = len(columns.get(target_status, []))

    source = columns.get(task.status, [])

    if target_status == task.status:
        old_index = next((i for i, t in enumerate(source) if t.id == task.id), -1)
        if old_index == -1 or old_index == target_index:
            return {}
        new_list = _array_move(source, old_index, target_index)
        return {"reorder": [{"id": t.id, "order": i} for i, t in enumerate(new_list)]}

    target = list(columns.get(target_status, []))
    target.insert(target_index, task)
    remaining_source = [t for t in source if t.id != task.id]
    return {
        "status_change": {"id": task.id, "status": target_status},
        "reorder": [
            *({"id": t.id, "order": i} for i, t in enumerate(target)),
            *({"id": t.id, "order": i} for i, t in enumerate(remaining_source)),
        ],
    }


def plan_tree_drag(tasks: list[Task], active_id: str, over_id: str | None) -> dict:
    """ツリードラッグの純粋な意思決定ロジック。同じ親の配下でのみ並べ替える。"""
    if not over_id or active_id == over_id:
        return {}

    active = next((t for t in tasks if t.id == active_id), None)
    over = next((t for t in tasks if t.id == over_id), None)
    if active is None or over is None:
        return {}
    if active.parent_id != over.parent_id:
        return {}

    siblings = sorted(
        (t for t in tasks if t.parent_id == active.parent_id), key=lambda t: t.order
    )
    old_index = next((i for i, t in enumerate(siblings) if t.id == active.id), -1)
    new_index = next((i for i, t in enumerate(siblings) if t.id == over.id), -1)
    if old_index == -1 or new_index == -1:
        return {}

    reordered = _array_move(siblings, old_index, new_index)
    return {"reorder": [{"id": t.id, "order": i} for i, t in enumerate(reordered)]}


def _is_descendant_or_self(tasks: list[Task], ancestor_id: str, task_id: str) -> bool:
    """task_id が ancestor_id 自身、またはその子孫かどうか。"""
    parent_of = {t.id: t.parent_id for t in tasks}
    current: str | None = task_id
    seen: set[str] = set()
    while current is not None and current not in seen:
        if current == ancestor_id:
            return True
        seen.add(current)
        current = parent_of.get(current)
    return False


def plan_row_drop(tasks: list[Task], active_id: str, target_id: str, zone: str) -> dict:
    """ガント行のドラッグ（親の付け替えを含む並べ替え）の純粋な意思決定ロジック。

    zone は、ドロップした行の上端 "before"（対象の直前に兄弟として挿入）・
    下端 "after"（直後に兄弟として挿入）・中央 "child"（対象の最後の子にする）。
    自分自身や自分の子孫の配下には移動できない（循環の防止）。

    戻り値: {"reorder": [{"id", "order", ["parent_id"]}, ...]}。変化が無ければ {}。
    親が変わる場合のみ、移動するタスクの要素に "parent_id" を含める。
    """
    if active_id == target_id or zone not in ("before", "after", "child"):
        return {}
    active = next((t for t in tasks if t.id == active_id), None)
    target = next((t for t in tasks if t.id == target_id), None)
    if active is None or target is None:
        return {}
    if _is_descendant_or_self(tasks, active_id, target_id):
        return {}

    new_parent = target.id if zone == "child" else target.parent_id
    siblings = sorted(
        (t for t in tasks if t.parent_id == new_parent and t.id != active_id),
        key=lambda t: t.order,
    )
    if zone == "child":
        index = len(siblings)
    else:
        target_index = next(i for i, t in enumerate(siblings) if t.id == target_id)
        index = target_index if zone == "before" else target_index + 1
    siblings.insert(index, active)

    parent_changed = active.parent_id != new_parent
    plan: list[dict] = []
    for i, t in enumerate(siblings):
        item: dict = {"id": t.id, "order": i}
        if t.id == active_id and parent_changed:
            item["parent_id"] = new_parent
        plan.append(item)

    if parent_changed:
        # 元の親の兄弟も詰め直す（順序の欠番を残さない）
        old_siblings = sorted(
            (t for t in tasks if t.parent_id == active.parent_id and t.id != active_id),
            key=lambda t: t.order,
        )
        plan.extend({"id": t.id, "order": i} for i, t in enumerate(old_siblings))
    else:
        old_siblings = sorted(
            (t for t in tasks if t.parent_id == active.parent_id), key=lambda t: t.order
        )
        if [t.id for t in old_siblings] == [t.id for t in siblings]:
            return {}
    return {"reorder": plan}
