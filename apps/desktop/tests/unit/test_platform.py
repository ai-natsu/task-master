"""OS ごとの違い（フォント・右クリック・データの保存場所）。"""

import importlib
import sys
from pathlib import Path

import pytest

from app.db import connection
from app.ui import platform_utils


def _reload(monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    return importlib.reload(platform_utils)


@pytest.fixture(autouse=True)
def _restore_platform_utils():
    yield
    importlib.reload(platform_utils)


def test_windows_uses_yu_gothic_and_button_3(monkeypatch):
    module = _reload(monkeypatch, "win32")
    assert module.FONT_FAMILY == "Yu Gothic UI"
    assert module.RIGHT_CLICK_SEQUENCES == ("<Button-3>",)
    assert module.IS_WINDOWS and not module.IS_MAC


def test_mac_uses_hiragino_and_secondary_click_or_control_click(monkeypatch):
    module = _reload(monkeypatch, "darwin")
    assert module.FONT_FAMILY == "Hiragino Sans"
    assert module.RIGHT_CLICK_SEQUENCES == ("<Button-2>", "<Control-Button-1>")
    assert module.IS_MAC and not module.IS_WINDOWS


def test_mac_app_stores_data_in_application_support(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setitem(connection.__dict__, "__compiled__", True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    data_dir = connection.get_app_dir()
    assert data_dir == tmp_path / "Library" / "Application Support" / "TaskMaster"
    assert data_dir.is_dir()


def test_windows_only_api_is_not_used_on_other_platforms(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("NUITKA_ONEFILE_PARENT", "1234")
    assert connection._onefile_parent_dir() is None
