import tempfile
from pathlib import Path

import pytest

from app.db.connection import connect


@pytest.fixture
def conn():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        c = connect(db_path)
        yield c
        c.close()


@pytest.fixture
def statuses(conn):
    """TODO(未完了)/DONE(完了)の2ステータスを投入する。"""
    with conn:
        conn.execute(
            'INSERT INTO "Status" (id, label, color, "order", isDone) VALUES '
            "('TODO', '未着手', '#64748b', 0, 0), "
            "('DONE', '完了', '#10b981', 1, 1)"
        )
    return ("TODO", "DONE")


@pytest.fixture(scope="session")
def app_window(tmp_path_factory):
    """実際のアプリ画面（AppWindow）。GUI テスト（tests/gui・tests/e2e）で共有する。

    一時の DB を使い、開発用の taskmaster.db には触れない。画面を開けない環境ではスキップする。
    """
    import customtkinter as ctk
    from customtkinter.windows.widgets.theme import ThemeManager

    from app import i18n
    from app.db.connection import ensure_default_statuses
    from app.ui import theme
    from app.ui.app_window import AppWindow

    ctk.set_appearance_mode("light")
    ThemeManager.theme["CTkFont"]["family"] = theme.FONT_FAMILY
    conn = connect(tmp_path_factory.mktemp("gui") / "gui.db")
    ensure_default_statuses(conn)
    i18n.set_language("ja")
    try:
        app = AppWindow(conn)
    except Exception as exc:  # ディスプレイが無い環境など
        conn.close()
        pytest.skip(f"画面を開けない環境のため、GUI テストをスキップ: {exc}")
    app.update()
    yield app
    app.destroy()
    conn.close()

