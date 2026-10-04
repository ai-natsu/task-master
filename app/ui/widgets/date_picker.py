"""日付入力欄とカレンダー（tkcalendar を使わない、自前の部品）。

- 入力欄に "2026-10-04" の形式で直接入力できる（Enter・フォーカス移動で確定）。
  日付として正しくない文字は、直前の正しい日付に戻す。
- 右のカレンダーのアイコンを押すと、カレンダーが開く。
  月曜始まり、土曜は青、日曜・祝日は赤。
- 年・月の見出しと曜日は、表示言語（日本語／英語）に合わせる。
"""

import datetime
import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image, ImageDraw

from app import i18n
from app.logic.calendar_grid import (
    WEEKDAY_NAMES,
    day_kind,
    month_grid,
    month_title,
    parse_date,
    shift_month,
    shift_year,
)
from app.ui import theme

_FONT = (theme.FONT_FAMILY, 11)
_BORDER = "#94a3b8"        # ポップアップの外枠・格子線
_HEADER_BG = "#475569"     # 年月の見出し（slate-600）
_WEEKDAY_BG = "#e2e8f0"    # 曜日の行（slate-200）
_CELL_BG = "#ffffff"
_OTHER_MONTH_FG = "#94a3b8"
_KIND_COLORS = {           # (文字色, 背景色)
    "saturday": ("#2563eb", "#eff6ff"),
    "holiday": ("#dc2626", "#fef2f2"),
}
_ICON_COLOR = "#6366f1"


def _calendar_icon(size: int, color: str) -> Image.Image:
    """正方形のカレンダーのアイコン（輪郭・上部の 2 本のタブ・見出しの罫線）を描く。"""
    scale = 6
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin, top = s * 0.12, s * 0.22
    line_width = max(round(s * 0.045), 1)
    tab_w = s * 0.07
    for cx in (s * 0.30, s * 0.70):
        draw.rounded_rectangle(
            [cx - tab_w / 2, s * 0.06, cx + tab_w / 2, top + s * 0.06],
            radius=tab_w / 2, fill=color,
        )
    draw.rounded_rectangle(
        [margin, top, s - margin, s - margin], radius=s * 0.10, outline=color, width=line_width
    )
    header_y = top + (s - margin - top) * 0.30
    draw.line(
        [margin + line_width / 2, header_y, s - margin - line_width / 2, header_y],
        fill=color, width=line_width,
    )
    return img.resize((size, size), Image.LANCZOS)


class CalendarPopup(tk.Toplevel):
    """月のカレンダー。日付を押すと on_select を呼んで閉じる。外側のクリック・Esc で閉じる。"""

    def __init__(
        self,
        anchor: tk.Widget,
        selected: datetime.date,
        holidays: Callable[[], set[str]],
        on_select: Callable[[datetime.date], None],
    ) -> None:
        super().__init__(anchor)
        self.overrideredirect(True)
        self.configure(bg=_BORDER)
        self._anchor = anchor
        self._selected = selected
        self._holidays = holidays
        self._on_select = on_select
        self._year, self._month = selected.year, selected.month
        self._today = datetime.date.today()
        self._language = i18n.get_language()

        body = tk.Frame(self, bg=_CELL_BG)
        body.pack(padx=1, pady=1)
        self._build_header(body)
        self._build_grid(body)
        self._render()

        self.update_idletasks()
        self._place()
        self._toplevel = anchor.winfo_toplevel()
        self._outside_id = self._toplevel.bind("<Button-1>", self._on_outside_click, add="+")
        self._toplevel.bind("<Escape>", lambda _e: self.close(), add="+")
        self.bind("<Escape>", lambda _e: self.close())

    # ---- 見出し（◀ 2026年 ▶ ◀ 10月 ▶）
    def _build_header(self, parent: tk.Frame) -> None:
        header = tk.Frame(parent, bg=_HEADER_BG)
        header.pack(fill="x")
        self._year_label = self._header_part(header, -1, +1, self._shift_year)
        self._month_label = self._header_part(header, -1, +1, self._shift_month)

    def _header_part(self, header, minus: int, plus: int, shift: Callable[[int], None]) -> tk.Label:
        part = tk.Frame(header, bg=_HEADER_BG)
        part.pack(side="left", expand=True, fill="x", padx=2, pady=3)
        for text, delta, side in (("◀", minus, "left"), ("▶", plus, "right")):
            btn = tk.Label(part, text=text, bg=_HEADER_BG, fg="white", font=(theme.FONT_FAMILY, 9),
                           cursor="hand2", padx=4)
            btn.pack(side=side)
            btn.bind("<Button-1>", lambda _e, d=delta: shift(d))
        label = tk.Label(part, bg=_HEADER_BG, fg="white", font=_FONT)
        label.pack(side="left", expand=True)
        return label

    def _shift_year(self, delta: int) -> None:
        self._year, self._month = shift_year(self._year, self._month, delta)
        self._render()

    def _shift_month(self, delta: int) -> None:
        self._year, self._month = shift_month(self._year, self._month, delta)
        self._render()

    # ---- 曜日の行と、6 週 × 7 日の格子
    def _build_grid(self, parent: tk.Frame) -> None:
        grid = tk.Frame(parent, bg=_BORDER)
        grid.pack()
        self._weekday_labels = []
        for col in range(7):
            label = tk.Label(grid, bg=_WEEKDAY_BG, width=4, font=_FONT)
            label.grid(row=0, column=col, padx=(0, 1), pady=(0, 1), sticky="nsew")
            self._weekday_labels.append(label)
        self._day_labels: list[list[tk.Label]] = []
        for row in range(6):
            cells = []
            for col in range(7):
                cell = tk.Label(grid, width=4, font=_FONT, cursor="hand2")
                cell.grid(row=row + 1, column=col, padx=(0, 1), pady=(0, 1), sticky="nsew")
                cell.bind("<Button-1>", self._on_pick)
                cells.append(cell)
            self._day_labels.append(cells)

    def _render(self) -> None:
        year_text, month_text = month_title(self._year, self._month, self._language)
        self._year_label.configure(text=year_text)
        self._month_label.configure(text=month_text)
        for label, name in zip(self._weekday_labels, WEEKDAY_NAMES[self._language], strict=True):
            label.configure(text=name)
        holidays = self._holidays()
        for row, week in enumerate(month_grid(self._year, self._month)):
            for col, day in enumerate(week):
                cell = self._day_labels[row][col]
                cell._date = day  # type: ignore[attr-defined]
                in_month = day.month == self._month
                fg, bg = "#0f172a", _CELL_BG
                kind = day_kind(day, holidays)
                if kind is not None:
                    fg, bg = _KIND_COLORS[kind]
                if not in_month:
                    fg = _OTHER_MONTH_FG
                    bg = _CELL_BG if kind is None else bg
                font = _FONT
                if day == self._selected:
                    fg, bg = "white", theme.ACCENT
                elif day == self._today:
                    font = (theme.FONT_FAMILY, 11, "bold", "underline")
                cell.configure(text=str(day.day), fg=fg, bg=bg, font=font)

    def _on_pick(self, event) -> None:
        day = event.widget._date
        self.close()
        self._on_select(day)

    # ---- 位置・閉じる
    def _place(self) -> None:
        x = self._anchor.winfo_rootx()
        y = self._anchor.winfo_rooty() + self._anchor.winfo_height()
        height = self.winfo_reqheight()
        if y + height > self.winfo_screenheight():  # 画面の下にはみ出すときは、入力欄の上に出す
            y = max(self._anchor.winfo_rooty() - height, 0)
        self.geometry(f"+{x}+{y}")

    def _on_outside_click(self, event) -> None:
        if str(event.widget).startswith(str(self)):
            return
        self.close()

    def close(self) -> None:
        if not self.winfo_exists():
            return
        try:
            self._toplevel.unbind("<Button-1>", self._outside_id)
        except tk.TclError:
            pass
        self.destroy()


class DatePicker(ctk.CTkFrame):
    """日付の入力欄 + カレンダーを開くボタン。`get_date()` / `set_date()` で日付を扱う。

    command: 日付が選ばれた・入力で確定したときに呼ぶ関数。
    holidays: 呼ぶたびに、最新の祝日（"YYYY-MM-DD" の集合）を返す関数
    （設定画面での祝日の変更を、カレンダーに反映するため）。
    """

    def __init__(
        self,
        master,
        date: datetime.date | None = None,
        holidays: Callable[[], set[str]] | None = None,
        command: Callable[[], None] | None = None,
        width: int = 84,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._holidays = holidays or (lambda: set())
        self._command = command
        self._date = date or datetime.date.today()
        self._popup: CalendarPopup | None = None
        self._text = tk.StringVar(value=self._date.isoformat())

        self.entry = ctk.CTkEntry(self, width=width, textvariable=self._text, font=_FONT)
        self.entry.pack(side="left")
        self._icon = ctk.CTkImage(light_image=_calendar_icon(44, _ICON_COLOR), size=(22, 22))
        self.button = ctk.CTkButton(
            self, text="", image=self._icon, width=30, height=28, fg_color="transparent",
            hover_color=("#e2e8f0", "#334155"), command=self.open_calendar,
        )
        self.button.pack(side="left", padx=(2, 0))
        self.entry.bind("<Return>", lambda _e: self._commit())
        self.entry.bind("<FocusOut>", lambda _e: self._commit())

    # ---- 日付の取得・設定
    def get_date(self) -> datetime.date:
        self._commit(notify=False)
        return self._date

    def set_date(self, date: datetime.date) -> None:
        self._date = date
        self._text.set(date.isoformat())

    def _commit(self, notify: bool = True) -> None:
        """入力欄の文字を日付として確定する。日付として正しくない文字は、直前の日付に戻す。"""
        parsed = parse_date(self._text.get())
        if parsed is None:
            self._text.set(self._date.isoformat())
            return
        changed = parsed != self._date or self._text.get() != parsed.isoformat()
        self._date = parsed
        self._text.set(parsed.isoformat())
        if notify and changed and self._command:
            self._command()

    # ---- カレンダー
    def open_calendar(self) -> None:
        if str(self.entry.cget("state")) == "disabled":
            return
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.close()
            return
        self._commit(notify=False)
        self._popup = CalendarPopup(self.entry, self._date, self._holidays, self._on_calendar_pick)

    def _on_calendar_pick(self, date: datetime.date) -> None:
        self.set_date(date)
        if self._command:
            self._command()

    # ---- 有効・無効
    def configure(self, require_redraw: bool = False, **kwargs) -> None:
        state = kwargs.pop("state", None)
        if state is not None:
            self.entry.configure(state=state)
            self.button.configure(state=state)
        if kwargs or require_redraw:
            super().configure(require_redraw=require_redraw, **kwargs)
