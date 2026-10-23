"""配布用 zip の作成。

`python packaging/build_zip.py` から呼ぶ。ビルド済みの TaskMaster.exe と、利用者向けの
README・ライブラリのライセンス表記・祝日 CSV の例を `TaskMaster/` フォルダにまとめて zip にする。
解凍すると `TaskMaster/` フォルダができ、その中の exe をそのまま起動できる。
データ（taskmaster.db）は exe と同じフォルダに初回起動時に作られるので、zip には含めない。

パッケージ名 `packaging` は、依存ライブラリ（packaging）と名前が衝突するため、
このファイルは import ではなくパス指定で読み込む（テストも同様）。
"""

import importlib.metadata
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "packaging" / "dist"
FILES = ROOT / "packaging" / "dist_files"
FOLDER_NAME = "TaskMaster"

# exe に同梱される実行時ライブラリ（pyproject の dependencies と、その依存先で実際に使うもの）
BUNDLED_PACKAGES = [
    "customtkinter",
    "darkdetect",
    "packaging",
    "pillow",
    "charset-normalizer",
]

# Python 本体と Tcl/Tk は pip のパッケージではないので、出典だけを記載する
RUNTIME_NOTICES = """\
Python
  Python Software Foundation License
  https://docs.python.org/3/license.html

Tcl/Tk（画面の部品）
  BSD 形式のライセンス
  https://www.tcl-lang.org/software/tcltk/license.html
"""


def read_version() -> str:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


def _license_files(dist: importlib.metadata.Distribution) -> list[tuple[str, str]]:
    """パッケージ付属のライセンス文書（LICENSE / COPYING / NOTICE など）を (名前, 本文) で返す。"""
    found: list[tuple[str, str]] = []
    for file in dist.files or []:
        upper = file.name.upper()
        if upper.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE", "AUTHORS")):
            try:
                text = file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            found.append((file.name, text.strip()))
    return found


def _license_name(meta) -> str:
    return meta.get("License-Expression") or meta.get("License") or "（下記の文書を参照）"


def build_notices(packages: list[str] = BUNDLED_PACKAGES) -> str:
    """THIRD_PARTY_NOTICES.txt の本文（各パッケージの名前・版・ライセンス表記）。"""
    lines = [
        "TaskMaster が利用しているライブラリのライセンス表記",
        "=" * 52,
        "",
        "TaskMaster.exe には、次のオープンソースのライブラリが含まれています。",
        "各ライブラリは、それぞれのライセンスに従って利用しています。",
        "",
        RUNTIME_NOTICES,
    ]
    for name in packages:
        dist = importlib.metadata.distribution(name)
        meta = dist.metadata
        lines += [
            "-" * 52,
            f"{meta['Name']} {dist.version}",
            f"  ライセンス: {_license_name(meta)}",
        ]
        if meta.get("Home-page"):
            lines.append(f"  {meta['Home-page']}")
        for filename, text in _license_files(dist):
            lines += ["", f"[{filename}]", text]
        lines.append("")
    return "\n".join(lines)


def _write_text(path: Path, text: str) -> None:
    """Windows のメモ帳でも読めるよう、UTF-8（BOM つき）・CRLF で書く。"""
    normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(normalized.encode("utf-8-sig"))


def stage_release(exe_path: Path, stage_dir: Path, version: str) -> Path:
    """stage_dir/TaskMaster/ に、配布するファイルをそろえる。作ったフォルダを返す。"""
    if not exe_path.exists():
        raise FileNotFoundError(f"TaskMaster.exe が見つかりません: {exe_path}")
    folder = stage_dir / FOLDER_NAME
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)

    shutil.copy2(exe_path, folder / "TaskMaster.exe")
    readme = (FILES / "README.txt").read_text(encoding="utf-8").replace("{version}", version)
    _write_text(folder / "README.txt", readme)
    _write_text(folder / "THIRD_PARTY_NOTICES.txt", build_notices())
    # TaskMaster 自体のライセンス（AGPL-3.0）。メモ帳で読めるよう .txt にして同梱する
    _write_text(folder / "LICENSE.txt", (ROOT / "LICENSE").read_text(encoding="utf-8"))
    shutil.copy2(FILES / "holidays_sample.csv", folder / "holidays_sample.csv")
    return folder


def find_mac_app(dist: Path = DIST) -> Path:
    """Nuitka が作った .app（フォルダ）を探す。"""
    apps = sorted(dist.glob("*.app"))
    if not apps:
        raise FileNotFoundError(f".app が見つかりません: {dist}")
    return apps[0]


def stage_release_mac(app_path: Path, stage_dir: Path, version: str) -> Path:
    """Mac 版：stage_dir/TaskMaster/ に、TaskMaster.app と、同梱する文書をそろえる。"""
    if not app_path.exists():
        raise FileNotFoundError(f"TaskMaster.app が見つかりません: {app_path}")
    folder = stage_dir / FOLDER_NAME
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)

    # .app の中には、実行ファイルの権限とシンボリックリンクがあるので、そのままコピーする
    shutil.copytree(app_path, folder / "TaskMaster.app", symlinks=True)
    readme = (FILES / "README_mac.txt").read_text(encoding="utf-8").replace("{version}", version)
    _write_text(folder / "README.txt", readme)
    _write_text(folder / "THIRD_PARTY_NOTICES.txt", build_notices())
    _write_text(folder / "LICENSE.txt", (ROOT / "LICENSE").read_text(encoding="utf-8"))
    shutil.copy2(FILES / "holidays_sample.csv", folder / "holidays_sample.csv")
    return folder


def make_zip_mac(folder: Path, zip_path: Path) -> Path:
    """Mac 版の zip。実行ファイルの権限が消えないよう、zipfile ではなく ditto で作る。"""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    subprocess.run(
        ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(folder), str(zip_path)],
        check=True,
    )
    return zip_path


def build_release_mac(app_path: Path | None = None, out_dir: Path | None = None) -> Path:
    version = read_version()
    app = app_path or find_mac_app()
    out = out_dir or DIST
    folder = stage_release_mac(app, out, version)
    return make_zip_mac(folder, out / f"TaskMaster-{version}-mac.zip")


def make_zip(folder: Path, zip_path: Path) -> Path:
    """folder を、フォルダ名ごと（解凍すると TaskMaster/ ができる形で）zip にする。"""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(folder.parent).as_posix())
    return zip_path


def build_release(exe_path: Path | None = None, out_dir: Path | None = None) -> Path:
    version = read_version()
    exe = exe_path or DIST / "TaskMaster.exe"
    out = out_dir or DIST
    folder = stage_release(exe, out, version)
    return make_zip(folder, out / f"TaskMaster-{version}-win64.zip")
