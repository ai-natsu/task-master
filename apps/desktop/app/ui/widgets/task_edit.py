"""タスクの作成・編集（フォームの表示と保存、親タスク変更の反映）。ツリー・カンバン・ガントで共通。

保存はフォームの中で行い、失敗（親タスクの循環など）はフォームを閉じずに赤字で表示する。
"""

from app.db.tasks import create_task, list_tasks, move_task, update_task
from app.ui.widgets.task_form_dialog import ask_task_form


def create_task_via_form(app, project_id: str, parent_id: str | None = None) -> bool:
    """新規作成フォームを開き、保存できたら True。親タスクはフォームで選んだ値を使う。"""

    def save(result: dict) -> None:
        data = {k: v for k, v in result.items() if k != "parent_id"}
        create_task(app.conn, project_id=project_id, parent_id=result["parent_id"], **data)

    return ask_task_form(app, app.conn, project_id, parent_id=parent_id, on_save=save) is not None


def edit_task(app, project_id: str, task) -> bool:
    """編集フォームを開き、保存できたら True。

    フォームで「親タスク」を変えた場合は、新しい親の最後の子として付け替える
    （どのビューから編集しても同じ結果になるよう、ここに集約している）。
    """

    def save(result: dict) -> None:
        data = {k: v for k, v in result.items() if k != "parent_id"}
        new_parent_id = result["parent_id"]
        if new_parent_id != task.parent_id:
            siblings = [
                x for x in list_tasks(app.conn, project_id=project_id)
                if x.parent_id == new_parent_id and x.id != task.id
            ]
            order = max((x.order for x in siblings), default=-1) + 1
            # 循環になる場合は CycleError（保存前に失敗し、フォームに表示される）
            move_task(app.conn, task.id, parent_id=new_parent_id, order=order)
        update_task(app.conn, task.id, **data)

    return ask_task_form(app, app.conn, project_id, task=task, on_save=save) is not None
