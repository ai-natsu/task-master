"""OS ごとの違い（Windows / Mac）を 1 か所にまとめる。

- 日本語のフォント：Windows は Yu Gothic UI、Mac は Hiragino Sans。
- 右クリック：Windows・Linux は Button-3。Mac は、マウスの副ボタンが Button-2、
  トラックパッドの「Control + クリック」が Control-Button-1 になる。
"""

import sys
import tkinter as tk
from collections.abc import Callable

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

# 日本語のグリフを持つ、その OS の標準のゴシック体
FONT_FAMILY = "Hiragino Sans" if IS_MAC else "Yu Gothic UI"

# 右クリックにあたる操作のイベント
RIGHT_CLICK_SEQUENCES = ("<Button-2>", "<Control-Button-1>") if IS_MAC else ("<Button-3>",)


def bind_right_click(widget: tk.Misc, handler: Callable) -> None:
    """widget の右クリック（Mac は副ボタン・Control + クリック）に handler を結びつける。"""
    for sequence in RIGHT_CLICK_SEQUENCES:
        widget.bind(sequence, handler)
