"""TaskMaster デスクトップ版エントリポイント。"""

import customtkinter as ctk
from customtkinter.windows.widgets.theme import ThemeManager

from app.db.connection import connect, ensure_default_statuses
from app.ui import theme
from app.ui.app_window import AppWindow


def main() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    # CustomTkinter既定の"Roboto"は旧Web版(Segoe UI)と混在すると見た目が
    # 揃わないため、familyを指定していない全CTkFont呼び出しに反映される
    # デフォルトフォントをここで一括変更する。
    ThemeManager.theme["CTkFont"]["family"] = theme.FONT_FAMILY
    ctk.set_widget_scaling(1.2)

    conn = connect()
    ensure_default_statuses(conn)
    app = AppWindow(conn)
    try:
        app.mainloop()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
