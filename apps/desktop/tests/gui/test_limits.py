"""入力欄の文字数の上限（app/ui/widgets/limits.py）。V1 の CT「入力値のチェック」に相当。"""


import customtkinter as ctk
import pytest

from app.constants import LIMITS
from app.ui.widgets.limits import limit_entry, limit_textbox

pytestmark = pytest.mark.gui


@pytest.fixture
def host(app_window):
    frame = ctk.CTkFrame(app_window)
    yield frame
    frame.destroy()


def _type(entry: ctk.CTkEntry, text: str) -> None:
    """キーボードで 1 文字ずつ入力した状態にする（上限を超えた入力は受け付けられない）。"""
    for ch in text:
        entry._entry.insert("end", ch)


def test_limit_values_match_the_spec():
    # 仕様（docs/BASIC_DESIGN.md）。V1 の client/src/constants/limits.ts と同じ値
    assert LIMITS == {
        "project_name": 200,
        "project_description": 2000,
        "task_title": 300,
        "task_description": 5000,
        "status_label": 50,
        "tag_name": 50,
        "holiday_name": 100,
    }


@pytest.mark.parametrize(
    "key", ["project_name", "task_title", "tag_name", "status_label", "holiday_name"]
)
def test_entry_accepts_exactly_the_limit_and_rejects_more(host, key):
    entry = ctk.CTkEntry(host)
    limit_entry(entry, key)
    _type(entry, "あ" * (LIMITS[key] + 10))
    assert len(entry.get()) == LIMITS[key]


def test_entry_paste_is_truncated_to_the_limit(host, app_window):
    entry = ctk.CTkEntry(host)
    limit_entry(entry, "tag_name")
    host.grid(row=99, column=0)
    entry.pack()
    app_window.update()
    entry._entry.focus_force()
    host.clipboard_clear()
    host.clipboard_append("x" * 80)
    entry._entry.event_generate("<<Paste>>")
    assert entry.get() == "x" * 50


def test_textbox_blocks_typing_beyond_the_limit(host):
    box = ctk.CTkTextbox(host)
    limit_textbox(box, "project_description")
    box.insert("1.0", "a" * LIMITS["project_description"])
    inner = box._textbox
    # 上限ちょうどのとき、文字を入力するキーは受け付けない（"break"）
    assert inner.bind("<KeyPress>")  # ハンドラが設定されている
    handler_result = inner.event_generate("<KeyPress>", keysym="a")  # 描画前でも例外にならないこと
    assert handler_result is None
    assert len(box.get("1.0", "end-1c")) == LIMITS["project_description"]


def test_textbox_paste_is_truncated_to_the_limit(host):
    box = ctk.CTkTextbox(host)
    limit_textbox(box, "project_description")
    box.insert("1.0", "a" * (LIMITS["project_description"] - 3))
    host.clipboard_clear()
    host.clipboard_append("b" * 50)
    box._textbox.event_generate("<<Paste>>")
    text = box.get("1.0", "end-1c")
    assert len(text) == LIMITS["project_description"]
    assert text.endswith("bbb")
