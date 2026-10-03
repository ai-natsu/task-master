"""タスク編集（フォームの表示と保存、親タスク変更の反映）。ツリー・カンバン・ガントで共通。"""

from tkinter import messagebox

from app.db.errors import CycleError
from app.db.tasks import list_tasks, move_task, update_task
from app.i18n import t
from app.ui.widgets.task_form_dialog import ask_task_form


def edit_task(parent, app, project_id: str, task) -> bool:
    """編集フォームを開き、保存されたら更新する。何か保存したら True。

    フォームで「親タスク」を変えた場合は、新しい親の最後の子として付け替える
    （どのビューから編集しても同じ結果になるよう、ここに集約している）。
    """
    result = ask_task_form(app, app.conn, project_id, task=task)
    if not result:
        return False
    new_parent_id = result.pop("parent_id", task.parent_id)
    update_task(app.conn, task.id, **result)
    if new_parent_id != task.parent_id:
        siblings = [
            x for x in list_tasks(app.conn, project_id=project_id)
            if x.parent_id == new_parent_id and x.id != task.id
        ]
        order = max((x.order for x in siblings), default=-1) + 1
        try:
            move_task(app.conn, task.id, parent_id=new_parent_id, order=order)
        except CycleError:
            messagebox.showerror(
                t("エラー"),
                t("タスクを自分自身またはその配下には移動できません。"),
                parent=parent,
            )
    return True
