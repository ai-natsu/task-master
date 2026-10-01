"""紙のタブ風デザインのビュー切替タブ。

CTkButton/CTkSegmentedButtonは角丸を4隅均等にしか指定できないため、
「上角だけ丸く、下は本体（コンテンツ領域）と地続きに見せる」という
紙のタブ特有の形は表現できない。そのため、tkinter.Canvasに
PIL(Pillow)で生成した角丸画像を貼り付けて描画する
（gantt_chart_widget.pyのCanvas直接描画と同じ方針）。
"""

import tkinter as tk
import tkinter.font as tkfont

from PIL import Image, ImageDraw, ImageTk

from app.ui import theme

_TAB_H = 36
_PAD_X = 18
_RADIUS = 10
_GAP = 2

_ACTIVE_FILL = "#ffffff"
_INACTIVE_FILL = "#eef1f6"
_BORDER = "#e2e8f0"
_ACTIVE_TEXT = "#0f172a"
_INACTIVE_TEXT = "#64748b"
_BG = theme.BG[0]


def _rounded_top_image(
    width: int, height: int, radius: int, fill: str, outline: str
) -> Image.Image:
    """上角だけ丸く、下端は水平なタブ背景を描く。

    角丸矩形を縦に余分な高さで描き、下側の丸まった部分を切り落とす
    ことで「上だけ丸い」形にする。
    """
    scale = 4
    w, h, r = width * scale, height * scale, radius * scale
    full = Image.new("RGBA", (w, h + r), (0, 0, 0, 0))
    draw = ImageDraw.Draw(full)
    draw.rounded_rectangle(
        [0, 0, w - 1, h + r - 1], radius=r, fill=fill, outline=outline, width=scale
    )
    cropped = full.crop((0, 0, w, h))
    return cropped.resize((width, height), Image.LANCZOS)


class PaperTabs(tk.Canvas):
    def __init__(self, master, values: list[tuple[str, str]], command, font=None, **kwargs):
        self._values = values
        self._command = command
        self._font = font or tkfont.Font(family="Yu Gothic UI", size=12)
        self._current = values[0][0] if values else None
        self._images: dict[tuple[str, bool], ImageTk.PhotoImage] = {}
        self._tab_bounds: list[tuple[int, int, str]] = []

        width, height = self._measure(values)
        super().__init__(
            master, width=width, height=height, highlightthickness=0, bd=0,
            bg=kwargs.pop("bg", _BG), **kwargs,
        )
        self.bind("<Button-1>", self._on_click)
        self._redraw()

    def _measure(self, values: list[tuple[str, str]]) -> tuple[int, int]:
        total = 0
        for _key, label in values:
            total += self._font.measure(label) + _PAD_X * 2 + _GAP
        return max(total, 1), _TAB_H

    def set(self, key: str) -> None:
        if key == self._current:
            return
        self._current = key
        self._redraw()

    def get(self) -> str | None:
        return self._current

    def _tab_image(self, label: str, is_active: bool) -> tuple[ImageTk.PhotoImage, int]:
        tab_w = self._font.measure(label) + _PAD_X * 2
        cache_key = (label, is_active)
        if cache_key not in self._images:
            fill = _ACTIVE_FILL if is_active else _INACTIVE_FILL
            img = _rounded_top_image(tab_w, _TAB_H, _RADIUS, fill, _BORDER)
            self._images[cache_key] = ImageTk.PhotoImage(img)
        return self._images[cache_key], tab_w

    def _redraw(self) -> None:
        self.delete("all")
        self._tab_bounds = []
        x = 0
        for key, label in self._values:
            is_active = key == self._current
            photo, tab_w = self._tab_image(label, is_active)
            self.create_image(x, 0, anchor="nw", image=photo)
            text_color = _ACTIVE_TEXT if is_active else _INACTIVE_TEXT
            self.create_text(
                x + tab_w / 2, _TAB_H / 2, text=label, fill=text_color, font=self._font,
            )
            if not is_active:
                # アクティブタブは本体(コンテンツ領域)と地続きに見せるため、
                # 下端の線は描かない。非アクティブタブだけ下端を線で閉じる。
                self.create_line(x, _TAB_H - 1, x + tab_w, _TAB_H - 1, fill=_BORDER)
            self._tab_bounds.append((x, x + tab_w, key))
            x += tab_w + _GAP

        total_width = max(x - _GAP, 1)
        self.configure(width=total_width, height=_TAB_H, scrollregion=(0, 0, total_width, _TAB_H))

    def _on_click(self, event) -> None:
        for x0, x1, key in self._tab_bounds:
            if x0 <= event.x < x1:
                if key != self._current:
                    self._current = key
                    self._redraw()
                    self._command(key)
                return
