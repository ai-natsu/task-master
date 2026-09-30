"""DB接続とスキーマ初期化。

データファイル(taskmaster.db)の配置場所は「実行ファイルと同じフォルダ」とする
(ユーザー指定)。Nuitka --onefile でビルドした exe は起動時に一時フォルダへ
自身を展開して実行するため、素の sys.argv[0] / __file__ は展開先の一時パスを
指してしまい使えない。

Nuitka がセットする環境変数 NUITKA_ONEFILE_PARENT は「元の exe のパス」では
なく「起動元(ブートストラップ)プロセスの PID」である（実機ビルドで確認済み・
Nuitka の OnefileBootstrap.c 参照）。そのため Windows API
(QueryFullProcessImageNameW) でその PID から実行ファイルのフルパスを逆引きし、
その親フォルダを使う。
"""

import ctypes
import os
import sqlite3
import sys
import uuid
from pathlib import Path

SCHEMA_VERSION = 3  # v2: Holiday テーブル追加 / v3: AppSetting テーブル追加
DB_FILENAME = "taskmaster.db"

DEFAULT_STATUSES = [
    ("TODO", "未着手", "#64748b", 0, 0),
    ("IN_PROGRESS", "進行中", "#6366f1", 1, 0),
    ("DONE", "完了", "#10b981", 2, 1),
    ("WITHDRAWN", "取下げ", "#94a3b8", 3, 1),
]

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _onefile_parent_dir() -> Path | None:
    pid_str = os.environ.get("NUITKA_ONEFILE_PARENT")
    if not pid_str:
        return None
    try:
        pid = int(pid_str)
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None
        try:
            buf = ctypes.create_unicode_buffer(32768)
            size = ctypes.c_uint32(len(buf))
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return None
            return Path(buf.value).resolve().parent
        finally:
            kernel32.CloseHandle(handle)
    except OSError:
        return None


def get_app_dir() -> Path:
    onefile_parent_dir = _onefile_parent_dir()
    if onefile_parent_dir is not None:
        return onefile_parent_dir
    if "__compiled__" in globals():
        return Path(sys.argv[0]).resolve().parent
    # 開発時（`python -m app.main` 等）はリポジトリルート直下に置く
    return Path(__file__).resolve().parent.parent.parent


def get_db_path() -> Path:
    return get_app_dir() / DB_FILENAME


def generate_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path if db_path is not None else get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current >= SCHEMA_VERSION:
        return
    schema_sql = (Path(__file__).resolve().parent / "schema.sql").read_text(encoding="utf-8")
    with conn:
        conn.executescript(schema_sql)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def ensure_default_statuses(conn: sqlite3.Connection) -> None:
    """ステータスが1件も無い場合のみデフォルト値を投入する（非破壊的）。

    アプリ起動時(app/main.py)からのみ呼び出す。データ層のテストや seed.py は
    「素のスキーマだけ適用された状態」を前提にするため、connect()/_ensure_schema
    には含めない。
    """
    count = conn.execute('SELECT COUNT(*) FROM "Status"').fetchone()[0]
    if count > 0:
        return
    with conn:
        conn.executemany(
            'INSERT INTO "Status" (id, label, color, "order", isDone) VALUES (?, ?, ?, ?, ?)',
            DEFAULT_STATUSES,
        )
