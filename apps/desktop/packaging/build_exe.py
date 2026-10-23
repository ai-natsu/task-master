"""Nuitka によるアプリのビルドスクリプト（Windows は単一 exe、Mac は .app）。

- Windows：Python 3.13 以降は Nuitka の MinGW64 の自動ダウンロードに対応していないため、
  C コンパイラには zig（--zig）を使う。単一の TaskMaster.exe を作る。
- Mac：Xcode の clang を使い、TaskMaster.app（アプリのフォルダ）を作る。Mac 用のビルドは、
  Mac 上でしかできない（GitHub Actions の macOS 環境で実行する）。

schema.sql は Python のソースではないため、--include-data-files で明示的に同梱する。
SQLite のデータファイル（taskmaster.db）は Nuitka に含めず、実行時に作る
（Windows は exe と同じフォルダ、Mac は ~/Library/Application Support/TaskMaster/）。

使い方: リポジトリのルートから `python packaging/build_exe.py` を実行する。
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IS_MAC = sys.platform == "darwin"


def build_command() -> list[str]:
    common = [
        sys.executable,
        "-m",
        "nuitka",
        "--assume-yes-for-downloads",
        "--enable-plugin=tk-inter",
        f"--include-data-files={ROOT / 'app' / 'db' / 'schema.sql'}=app/db/schema.sql",
        "--output-dir=packaging/dist",
        "--company-name=TaskMaster",
        "--product-name=TaskMaster",
    ]
    if IS_MAC:
        return common + [
            "--standalone",
            "--macos-create-app-bundle",
            f"--macos-app-icon={ROOT / 'app' / 'assets' / 'icon.icns'}",
            "--macos-app-name=TaskMaster",
            "--macos-app-version=2.0.0",
            "--output-filename=TaskMaster",
            str(ROOT / "app" / "main.py"),
        ]
    return common + [
        "--onefile",
        "--zig",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={ROOT / 'app' / 'assets' / 'icon.ico'}",
        f"--include-data-files={ROOT / 'app' / 'assets' / 'icon.ico'}=app/assets/icon.ico",
        "--output-filename=TaskMaster.exe",
        "--file-version=2.0.0.0",
        "--product-version=2.0.0.0",
        str(ROOT / "app" / "main.py"),
    ]


def main() -> None:
    cmd = build_command()
    print("実行コマンド:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
