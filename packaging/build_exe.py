"""Nuitkaによる単一exeビルドスクリプト。

Python 3.13以降はNuitkaのMinGW64自動ダウンロードに対応していないため、
Cコンパイラバックエンドにはzig(--zig)を使う。schema.sqlはPythonソースでは
ないため--include-data-filesで明示的に同梱する。SQLiteのデータファイル
(taskmaster.db)はNuitkaに含めず、exeと同じフォルダに実行時生成される。

使い方: リポジトリルートから `python packaging/build_exe.py` を実行する。
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--zig",
        "--assume-yes-for-downloads",
        "--enable-plugin=tk-inter",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={ROOT / 'app' / 'assets' / 'icon.ico'}",
        f"--include-data-files={ROOT / 'app' / 'db' / 'schema.sql'}=app/db/schema.sql",
        f"--include-data-files={ROOT / 'app' / 'assets' / 'icon.ico'}=app/assets/icon.ico",
        "--output-dir=packaging/dist",
        "--output-filename=TaskMaster.exe",
        "--company-name=TaskMaster",
        "--product-name=TaskMaster",
        "--file-version=2.0.0.0",
        "--product-version=2.0.0.0",
        str(ROOT / "app" / "main.py"),
    ]
    print("実行コマンド:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
