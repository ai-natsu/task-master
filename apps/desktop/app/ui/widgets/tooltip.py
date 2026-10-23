"""マウスオーバー時に少し遅れて表示するツールチップ（Canvas 上の要素にも使える）。"""

import tkinter as tk

from app.ui import theme

_DELAY_MS = 500
_OFFSET = (14, 18)


class Tooltip:
    """widget 上の任意の場所に、遅延付きでツールチップを出す。

    schedule() で表示を予約し、hide() で取り消す/閉じる。表示中に別のテキストで
    schedule() すると、いったん閉じてから予約し直す。
    """

    def __init__(self, widget: tk.Misc, delay_ms: int = _DELAY_MS):
        self._widget = widget
        self._delay_ms = delay_ms
        self._job: str | None = None
        self._window: tk.Toplevel | None = None

    def schedule(self, text: str, x_root: int, y_root: int) -> None:
        self.hide()
        self._job = self._widget.after(self._delay_ms, lambda: self._show(text, x_root, y_root))

    def hide(self) -> None:
        if self._job is not None:
            self._widget.after_cancel(self._job)
            self._job = None
        if self._window is not None:
            self._window.destroy()
            self._window = None

    def _show(self, text: str, x_root: int, y_root: int) -> None:
        self._job = None
        window = tk.Toplevel(self._widget)
        window.overrideredirect(True)
        try:
            window.attributes("-topmost", True)
        except tk.TclError:
            pass  # 一部環境では最前面指定が使えないため握りつぶす
        tk.Label(
            window, text=text, justify="left", background="#1e293b", foreground="#f8fafc",
            font=(theme.FONT_FAMILY, 10), padx=8, pady=4,
        ).pack()
        window.geometry(f"+{x_root + _OFFSET[0]}+{y_root + _OFFSET[1]}")
        self._window = window
