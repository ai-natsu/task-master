"""入力フォームの入力チェック（必須の赤字・文字数の上限）。V1 の CT「入力値のチェック」に相当。"""

import pytest

from app.constants import LIMITS
from app.db.projects import create_project
from app.ui.widgets.confirm_dialog import ConfirmDialog
from app.ui.widgets.project_form_dialog import ProjectFormDialog
from app.ui.widgets.task_form_dialog import TaskFormDialog

pytestmark = pytest.mark.gui

RED = "#dc2626"


def _type(entry, text: str) -> None:
    for ch in text:
        entry._entry.insert("end", ch)


@pytest.fixture
def project(app_window):
    return create_project(app_window.conn, "フォーム検証用")


@pytest.fixture
def project_form(app_window):
    dialog = ProjectFormDialog(app_window)
    app_window.update()
    yield dialog
    dialog.destroy()


@pytest.fixture
def task_form(app_window, project):
    dialog = TaskFormDialog(app_window, app_window.conn, project.id)
    app_window.update()
    yield dialog
    dialog.destroy()


class TestProjectForm:
    def test_empty_name_shows_required_error_and_does_not_save(self, project_form):
        project_form._submit()
        project_form.update()
        assert project_form._name_error.label.cget("text") == "名前を入力してください"
        assert project_form.name_entry.cget("border_color") == RED
        assert project_form.result is None

    def test_whitespace_only_name_is_rejected(self, project_form):
        project_form.name_entry.insert(0, "   ")
        project_form._submit()
        assert project_form._name_error.label.cget("text") == "名前を入力してください"
        assert project_form.result is None

    def test_error_disappears_when_the_user_types(self, project_form):
        project_form._submit()
        _type(project_form.name_entry, "A")
        project_form._name_error._on_key(None)
        assert project_form._name_error.label.winfo_manager() == ""

    def test_name_is_limited_to_200_characters(self, project_form):
        _type(project_form.name_entry, "あ" * 210)
        assert len(project_form.name_entry.get()) == LIMITS["project_name"] == 200

    def test_exact_limit_can_be_saved(self, project_form):
        _type(project_form.name_entry, "あ" * 200)
        project_form._submit()
        assert project_form.result is not None
        assert len(project_form.result["name"]) == 200


class TestTaskForm:
    def test_empty_title_shows_required_error(self, task_form):
        task_form._submit()
        task_form.update()
        assert task_form._title_error.label.cget("text") == "タイトルを入力してください"
        assert task_form.title_entry.cget("border_color") == RED
        assert task_form.result is None

    def test_title_is_limited_to_300_characters(self, task_form):
        _type(task_form.title_entry, "い" * 310)
        assert len(task_form.title_entry.get()) == LIMITS["task_title"] == 300

    def test_exact_limit_title_can_be_saved(self, task_form):
        _type(task_form.title_entry, "い" * 300)
        task_form._submit()
        assert task_form.result is not None
        assert len(task_form.result["title"]) == 300

    def test_new_tag_name_is_limited_to_50_characters(self, task_form, app_window):
        # プレースホルダは、入力欄にフォーカスが入ると消える（利用者が入力を始める状態にする）
        task_form.new_tag_entry._entry.focus_force()
        app_window.update()
        _type(task_form.new_tag_entry, "t" * 60)
        assert len(task_form.new_tag_entry.get()) == LIMITS["tag_name"] == 50

    def test_empty_new_tag_shows_required_error(self, task_form):
        task_form._add_tag()
        assert task_form.error_label.cget("text") == "名前を入力してください"


class TestConfirmDialog:
    def test_confirm_and_cancel(self, app_window):
        dialog = ConfirmDialog(app_window, "削除", "本当に削除しますか？")
        assert dialog.confirmed is False
        dialog._on_confirm()
        assert dialog.confirmed is True

        dialog = ConfirmDialog(app_window, "削除", "本当に削除しますか？")
        dialog._on_cancel()
        assert dialog.confirmed is False

    def test_confirm_label_can_be_customised(self, app_window):
        import customtkinter as ctk

        from tests.gui_support import find_widgets

        dialog = ConfirmDialog(app_window, "アーカイブ", "よろしいですか？", "アーカイブする")
        app_window.update()
        labels = [b.cget("text") for b in find_widgets(dialog, ctk.CTkButton)]
        assert "アーカイブする" in labels
        assert "キャンセル" in labels
        dialog.destroy()
