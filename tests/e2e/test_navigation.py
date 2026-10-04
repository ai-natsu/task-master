"""画面遷移・操作のテスト（アプリ全体を実際に動かす）。V1 の e2e/navigation.spec.ts に相当。

番号は docs/BASIC_DESIGN.md の「画面遷移表」の No に対応する。V2 はブラウザではないので、
戻る/進む・URL の直接入力は無い。
"""

import customtkinter as ctk
import pytest

from app.db.projects import create_project, get_project, list_projects
from app.ui import projects_list_view
from app.ui.dashboard_view import DashboardView
from app.ui.project_view import ProjectView
from app.ui.projects_list_view import ProjectsListView
from app.ui.settings_view import SettingsView
from app.ui.widgets.gantt_chart_widget import GanttChartWidget
from app.ui.widgets.kanban_board_widget import KanbanBoardWidget
from app.ui.widgets.project_form_dialog import ProjectFormDialog
from app.ui.widgets.task_form_dialog import TaskFormDialog
from app.ui.widgets.task_tree_widget import TaskTreeWidget
from tests.gui_support import click_tab, find_label, find_widgets, toplevels

pytestmark = pytest.mark.e2e

_seq = 0


def unique(prefix: str) -> str:
    global _seq
    _seq += 1
    return f"{prefix}{_seq}"


def click_button(root, text: str) -> None:
    """表示文字に text を含むボタンを押す。"""
    for btn in find_widgets(root, ctk.CTkButton):
        if text in (btn.cget("text") or ""):
            btn.invoke()
            return
    raise AssertionError(f"ボタン「{text}」が見つかりません")


def with_modal(app, action) -> None:
    """モーダルを開く操作（開いている間は戻らない）の前に、開いたモーダルを操作する処理を予約する。"""

    def _run() -> None:
        dialogs = toplevels(app)
        assert dialogs, "モーダルが開いていません"
        action(dialogs[-1])

    app.after(150, _run)


@pytest.fixture
def project(app_window):
    return create_project(app_window.conn, unique("遷移検証"))


class TestSidebar:
    def test_no1_to_3_sidebar_moves_between_screens(self, app_window):
        sidebar = app_window.sidebar
        sidebar.nav_buttons["projects"].invoke()
        app_window.update()
        assert isinstance(app_window._current_view, ProjectsListView)
        sidebar.nav_buttons["dashboard"].invoke()
        app_window.update()
        assert isinstance(app_window._current_view, DashboardView)
        click_button(sidebar, "設定")
        app_window.update()
        assert isinstance(app_window._current_view, SettingsView)

    def test_no4_sidebar_project_name_opens_the_project(self, app_window, project):
        app_window.sidebar.refresh_projects()
        click_button(app_window.sidebar, project.name)
        app_window.update()
        view = app_window._current_view
        assert isinstance(view, ProjectView)
        assert view.project_id == project.id


class TestProjectScreens:
    def test_no6_project_list_name_opens_the_project(self, app_window, project):
        app_window.navigate("projects")
        app_window.update()
        label = find_label(app_window._current_view, project.name)
        assert label is not None
        # CTkLabel のクリックは、内側の tk.Label に届く
        inner = getattr(label, "_label", label)
        inner.event_generate("<Button-1>")
        app_window.update()
        assert isinstance(app_window._current_view, ProjectView)
        assert app_window._current_view.project_id == project.id

    def test_no3_view_switch_tree_kanban_gantt(self, app_window, project):
        app_window.navigate("project", project_id=project.id)
        app_window.update()
        view = app_window._current_view
        assert view.view_mode == "tree"
        assert isinstance(view._body, TaskTreeWidget)

        click_tab(view.view_switch, "kanban")
        app_window.update()
        assert view.view_mode == "kanban"
        assert isinstance(view._body, KanbanBoardWidget)

        click_tab(view.view_switch, "gantt")
        app_window.update()
        assert view.view_mode == "gantt"
        assert isinstance(view._body, GanttChartWidget)

        click_tab(view.view_switch, "tree")
        app_window.update()
        assert isinstance(view._body, TaskTreeWidget)


class TestModals:
    def test_no7_new_project_dialog_opens_and_can_be_cancelled(self, app_window):
        app_window.navigate("projects")
        app_window.update()
        seen = {}

        def action(dialog):
            seen["type"] = type(dialog)
            seen["title"] = dialog.title()
            dialog.destroy()

        with_modal(app_window, action)
        app_window._current_view._create()
        assert seen["type"] is ProjectFormDialog
        assert seen["title"] == "新しいプロジェクト"

    def test_no7_creating_a_project_adds_it_to_the_list(self, app_window):
        app_window.navigate("projects")
        app_window.update()
        name = unique("新規作成")

        def action(dialog):
            dialog.name_entry.insert(0, name)
            dialog._submit()

        with_modal(app_window, action)
        app_window._current_view._create()
        app_window.update()
        assert any(p.name == name for p in list_projects(app_window.conn))
        assert find_label(app_window._current_view, name) is not None

    def test_no8_edit_project_dialog_opens(self, app_window, project):
        app_window.navigate("projects")
        app_window.update()
        seen = {}

        def action(dialog):
            seen["title"] = dialog.title()
            seen["name"] = dialog.name_entry.get()
            dialog.destroy()

        with_modal(app_window, action)
        app_window._current_view._edit(get_project(app_window.conn, project.id))
        assert seen == {"title": "プロジェクトを編集", "name": project.name}

    def test_no9_new_task_dialog_opens_from_the_project_screen(self, app_window, project):
        app_window.navigate("project", project_id=project.id)
        app_window.update()
        seen = {}

        def action(dialog):
            seen["type"] = type(dialog)
            seen["title"] = dialog.title()
            dialog.destroy()

        with_modal(app_window, action)
        app_window._current_view._add_root_task()
        assert seen["type"] is TaskFormDialog
        assert seen["title"] == "新しいタスク"


class TestConfirmations:
    def test_no12_archive_and_restore_go_through_the_confirm_dialog(
        self, app_window, project, monkeypatch
    ):
        app_window.navigate("projects")
        app_window.update()
        view = app_window._current_view
        asked = []

        def decide(answer):
            def _ask(_parent, title, message, confirm_label=None):
                asked.append((title, confirm_label))
                return answer

            monkeypatch.setattr(projects_list_view, "ask_confirm", _ask)

        decide(False)
        view._toggle_archive(get_project(app_window.conn, project.id))
        # キャンセルなら変わらない
        assert get_project(app_window.conn, project.id).archived is False

        decide(True)
        view._toggle_archive(get_project(app_window.conn, project.id))
        assert get_project(app_window.conn, project.id).archived is True
        view._toggle_archive(get_project(app_window.conn, project.id))
        assert get_project(app_window.conn, project.id).archived is False
        assert asked == [
            ("プロジェクトをアーカイブ", "アーカイブする"),
            ("プロジェクトをアーカイブ", "アーカイブする"),
            ("プロジェクトを復元", "復元する"),
        ]

    def test_no12_delete_asks_first_and_cancel_keeps_the_project(
        self, app_window, project, monkeypatch
    ):
        app_window.navigate("projects")
        app_window.update()
        view = app_window._current_view
        monkeypatch.setattr(projects_list_view, "ask_confirm", lambda *a, **k: False)
        view._delete(get_project(app_window.conn, project.id))
        assert get_project(app_window.conn, project.id) is not None

        monkeypatch.setattr(projects_list_view, "ask_confirm", lambda *a, **k: True)
        view._delete(get_project(app_window.conn, project.id))
        assert get_project(app_window.conn, project.id) is None


class TestSettingsErrors:
    def test_empty_add_shows_required_errors(self, app_window):
        app_window.navigate("settings")
        app_window.update()
        view = app_window._current_view
        view._add_status()
        view._add_holiday()
        view._add_tag()
        assert view.error_label.cget("text") == "名前を入力してください"
        assert view.holiday_error_label.cget("text") == "名称を入力してください"
        assert view.tag_error_label.cget("text") == "名前を入力してください"
