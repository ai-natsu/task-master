import importlib.util
import zipfile
from pathlib import Path

import pytest

from app.db.holidays import parse_holiday_csv

RELEASE_PY = Path(__file__).resolve().parents[2] / "packaging" / "release.py"


@pytest.fixture(scope="module")
def release():
    # 「packaging」は依存ライブラリと名前が衝突するので、ファイルを直接読み込む
    spec = importlib.util.spec_from_file_location("release", RELEASE_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_exe(tmp_path):
    exe = tmp_path / "TaskMaster.exe"
    exe.write_bytes(b"MZ-fake-exe")
    return exe


def test_zip_unpacks_into_a_taskmaster_folder_with_everything_needed(release, fake_exe, tmp_path):
    zip_path = release.build_release(fake_exe, tmp_path / "out")
    assert zip_path.name == f"TaskMaster-{release.read_version()}-win64.zip"
    with zipfile.ZipFile(zip_path) as zf:
        names = sorted(zf.namelist())
    assert names == [
        "TaskMaster/LICENSE.txt",
        "TaskMaster/README.txt",
        "TaskMaster/THIRD_PARTY_NOTICES.txt",
        "TaskMaster/TaskMaster.exe",
        "TaskMaster/holidays_sample.csv",
    ]


def test_zip_does_not_contain_user_data(release, fake_exe, tmp_path):
    zip_path = release.build_release(fake_exe, tmp_path / "out")
    with zipfile.ZipFile(zip_path) as zf:
        assert not [n for n in zf.namelist() if n.endswith(".db")]


def test_readme_has_version_data_location_and_is_notepad_friendly(release, fake_exe, tmp_path):
    folder = release.stage_release(fake_exe, tmp_path / "out", "9.9.9")
    raw = (folder / "README.txt").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert b"\r\n" in raw
    text = raw.decode("utf-8-sig")
    assert "TaskMaster 9.9.9" in text
    assert "{version}" not in text
    assert "TaskMaster.exe と同じフォルダの「taskmaster.db」" in text


def test_notices_list_every_bundled_library_with_its_license(release):
    notices = release.build_notices()
    for name in ("customtkinter", "pillow", "charset-normalizer"):
        assert name.lower() in notices.lower()
    # GPL 系のライブラリ（tkcalendar）は使わない。TaskMaster 自体を、商用ライセンスでも提供するため
    assert "tkcalendar" not in notices.lower()
    assert "Python Software Foundation" in notices


def test_missing_exe_is_a_clear_error(release, tmp_path):
    with pytest.raises(FileNotFoundError, match="TaskMaster.exe"):
        release.stage_release(tmp_path / "nope.exe", tmp_path / "out", "1.0.0")


def test_sample_holiday_csv_can_be_imported_by_the_app(release):
    raw = (release.FILES / "holidays_sample.csv").read_bytes()
    rows = parse_holiday_csv(raw)
    assert len(rows) == 18
    assert ("2026-01-01", "元日") in rows
    assert all(date.startswith("2026-") for date, _name in rows)
