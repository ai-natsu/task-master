"""DB接続とスキーマ初期化。

データファイル(taskmaster.db)の配置場所は「実行ファイルと同じフォルダ」とする
(ユーザー指定)。Nuitka --onefile でビルドした exe は起動時に一時フォルダへ
展開されるため、素の sys.argv[0] は使えない場合がある。Nuitka が提供する
NUITKA_ONEFILE_PARENT 環境変数（元の exe があるフォルダを指す）を優先的に使う。
この経路は実機ビルド後の検証が必要（フェーズ8で確認）。
"""

import os
import sqlite3
import sys
import uuid
from pathlib import Path

SCHEMA_VERSION = 1
DB_FILENAME = "taskmaster.db"

DEFAULT_STATUSES = [
    ("TODO", "未着手", "#64748b", 0, 0),
    ("IN_PROGRESS", "進行中", "#6366f1", 1, 0),
    ("DONE", "完了", "#10b981", 2, 1),
    ("WITHDRAWN", "取下げ", "#94a3b8", 3, 1),
]


def get_app_dir() -> Path:
    onefile_parent = os.environ.get("NUITKA_ONEFILE_PARENT")
    if onefile_parent:
        return Path(onefile_parent).resolve()
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
