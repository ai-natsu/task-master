"""長い文字列を「...」で省略して表示するための部品。

Tk のラベルやボタンは、表示しきれない文字を単に切り捨てる（「...」を出せない）うえ、
文字の長さに合わせて親の幅まで広げてしまう。そのため、実際に使える幅を測って、
収まるように文字列を切り詰める。
"""

import tkinter as tk

import customtkinter as ctk

_ELLIPSIS = "..."


def ellipsize(text: str, font, max_px: float) -> str:
    """text が max_px（拡大率をかける前の幅）に収まるよう、末尾を「...」に置き換える。"""
    if font.measure(text) <= max_px:
        return text
    if font.measure(_ELLIPSIS) > max_px:
        return ""
    low, high = 0, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        if font.measure(text[:mid] + _ELLIPSIS) <= max_px:
            low = mid
        else:
            high = mid - 1
    return text[:low] + _ELLIPSIS


class EllipsisLabel(ctk.CTkLabel):
    """置かれた幅に合わせて、収まらない分を「...」で省略する 1 行ラベル。

    幅は親のレイアウト（pack の fill="x" など）で決まり、文字の長さでは広がらない。
    ウィンドウの幅を変えると、そのたびに省略の位置を引き直す。
    """

    def __init__(self, master, text: str, font=None, padding: int = 0, **kwargs):
        self._full_text = text
        self._ellipsis_font = font if font is not None else ctk.CTkFont()
        self._ellipsis_padding = padding
        self._shown: str | None = None
        kwargs.setdefault("anchor", "w")
        super().__init__(master, text="", font=self._ellipsis_font, width=1, **kwargs)
        tk.Misc.bind(self, "<Configure>", self._fit, add="+")

    def _fit(self, event) -> None:
        available = event.width / self._get_widget_scaling() - self._ellipsis_padding
        shown = ellipsize(self._full_text, self._ellipsis_font, available)
        if shown != self._shown:
            self._shown = shown
            self.configure(text=shown)
