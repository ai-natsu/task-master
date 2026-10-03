import tkinter as tk
import tkinter.font as tkfont

import pytest

from app.ui.widgets.ellipsis import ellipsize


@pytest.fixture(scope="module")
def font():
    root = tk.Tk()
    root.withdraw()
    yield tkfont.Font(root=root, family="Yu Gothic UI", size=12)
    root.destroy()


def test_short_text_is_unchanged(font):
    assert ellipsize("短い", font, 500) == "短い"


def test_long_text_is_cut_with_dots_and_fits(font):
    text = "とても長いプロジェクト名のサンプル" * 3
    shown = ellipsize(text, font, 150)
    assert shown.endswith("...")
    assert shown != text
    assert font.measure(shown) <= 150
    # 1文字多く残すと収まらない（最大限使っている）
    longer = text[: len(shown) - 3 + 1] + "..."
    assert font.measure(longer) > 150


def test_no_room_even_for_dots_gives_empty(font):
    assert ellipsize("あいうえお" * 10, font, 2) == ""
