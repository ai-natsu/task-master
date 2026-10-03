"""配布用 zip を作るスクリプト（ビルド → 同梱物をそろえる → zip）。

使い方（リポジトリルートから）:
    python packaging/build_zip.py              # exe をビルドしてから zip を作る（数分かかる）
    python packaging/build_zip.py --skip-build # ビルド済みの exe を使い、zip だけ作る

成果物: packaging/dist/TaskMaster-<version>-win64.zip（解凍すると TaskMaster/ フォルダができる）
"""

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    # 「packaging」は依存ライブラリと名前が衝突するので、ファイルを直接読み込む
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description="TaskMaster の配布用 zip を作る")
    parser.add_argument("--skip-build", action="store_true", help="exe のビルドを省略する")
    args = parser.parse_args()

    if not args.skip_build:
        _load("build_exe").main()
    zip_path = _load("release").build_release()
    print(f"作成しました: {zip_path}")


if __name__ == "__main__":
    main()
