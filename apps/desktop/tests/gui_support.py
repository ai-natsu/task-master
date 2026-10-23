"""GUI テスト（tests/gui・tests/e2e）で共通に使う補助。

Tk の画面を実際に作って検証する。画面を開けない環境（ディスプレイが無い CI など）では、
テストを自動でスキップする。
"""

import tkinter as tk

import customtkinter as ctk


def find_widgets(root, cls) -> list:
    """root の配下から、型が cls のウィジェットを全て集める。"""
    found = []
    for child in root.winfo_children():
        if isinstance(child, cls):
            found.append(child)
        found.extend(find_widgets(child, cls))
    return found


def find_label(root, text: str):
    """root の配下から、表示文字が text の CTkLabel（または EllipsisLabel）を探す。"""
    from app.ui.widgets.ellipsis import EllipsisLabel

    # 省略表示のラベルは、全文を _full_text に持つ（画面に出ている文字は省略されうる）
    for w in find_widgets(root, EllipsisLabel):
        if getattr(w, "_full_text", None) == text:
            return w
    for w in find_widgets(root, ctk.CTkLabel):
        try:
            if w.cget("text") == text:
                return w
        except (tk.TclError, ValueError):
            continue
    return None


def click_tab(tabs, key: str) -> None:
    """紙のタブ（PaperTabs）の、key のタブの中央をクリックする。"""
    for x0, x1, k in tabs._tab_bounds:
        if k == key:
            tabs.event_generate("<Button-1>", x=int((x0 + x1) / 2), y=5)
            return
    raise AssertionError(f"タブ {key} が見つかりません")


def toplevels(app) -> list:
    """アプリの上に開いているモーダル（CTkToplevel）。"""
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]
