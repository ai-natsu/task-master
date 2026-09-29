"""TaskMaster デスクトップ版エントリポイント。"""

import customtkinter as ctk

from app.db.connection import connect
from app.ui.app_window import AppWindow


def main() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    conn = connect()
    app = AppWindow(conn)
    try:
        app.mainloop()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
