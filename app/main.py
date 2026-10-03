"""TaskMaster デスクトップ版エントリポイント。"""

import customtkinter as ctk
from customtkinter.windows.widgets.theme import ThemeManager

from app import i18n
from app.db.connection import connect, ensure_default_statuses
from app.db.settings import get_setting
from app.ui import theme
from app.ui.app_window import AppWindow


def main() -> None:
    # ツリー・ガント・紙のタブなどの色はライト用に固定しているため、外観はライトに固定する
    # （OS がダークでも、一部だけダークになる混在を避ける）
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    # CustomTkinter既定の"Roboto"は日本語グリフを持たず代替表示が環境依存に
    # なるため、familyを指定していない全CTkFont呼び出しに反映されるデフォルト
    # フォントをここで日本語ゴシック体に一括変更する（詳細はtheme.py参照）。
    ThemeManager.theme["CTkFont"]["family"] = theme.FONT_FAMILY
    ctk.set_widget_scaling(1.2)

    conn = connect()
    ensure_default_statuses(conn)
    i18n.set_language(get_setting(conn, "language", "ja"))
    app = AppWindow(conn)
    try:
        app.mainloop()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
