"""データ層の入力検査（文字数の上限・必須）。V1 の API の zod スキーマ（400）に相当。"""

import pytest

from app.constants import LIMITS
from app.db.errors import ValidationError
from app.db.holidays import bulk_upsert_holidays, upsert_holiday
from app.db.projects import create_project, update_project
from app.db.statuses import create_status, update_status
from app.db.tags import create_tag, update_tag
from app.db.tasks import create_task, update_task


def long(key: str, extra: int = 1) -> str:
    return "あ" * (LIMITS[key] + extra)


class TestProject:
    def test_name_limit_boundary(self, conn):
        create_project(conn, long("project_name", 0))  # 上限ちょうど
        with pytest.raises(ValidationError) as exc:
            create_project(conn, long("project_name"))
        assert "名前は1〜200文字" in str(exc.value)

    def test_empty_name_is_rejected(self, conn):
        with pytest.raises(ValidationError):
            create_project(conn, "")

    def test_description_limit(self, conn):
        create_project(conn, "p", description="い" * 2000)
        with pytest.raises(ValidationError) as exc:
            create_project(conn, "p", description=long("project_description"))
        assert "説明は2000文字以内" in str(exc.value)

    def test_update_checks_too(self, conn):
        project = create_project(conn, "p")
        with pytest.raises(ValidationError):
            update_project(conn, project.id, name=long("project_name"))


class TestTask:
    def test_title_limit_boundary(self, conn, statuses):
        project = create_project(conn, "p")
        create_task(conn, long("task_title", 0), project.id)
        with pytest.raises(ValidationError) as exc:
            create_task(conn, long("task_title"), project.id)
        assert "タイトルは1〜300文字" in str(exc.value)

    def test_description_limit(self, conn, statuses):
        project = create_project(conn, "p")
        create_task(conn, "t", project.id, description="う" * 5000)
        with pytest.raises(ValidationError):
            create_task(conn, "t", project.id, description=long("task_description"))

    def test_update_checks_title_and_description(self, conn, statuses):
        task = create_task(conn, "t", create_project(conn, "p").id)
        with pytest.raises(ValidationError):
            update_task(conn, task.id, title=long("task_title"))
        with pytest.raises(ValidationError):
            update_task(conn, task.id, description=long("task_description"))


class TestTagStatusHoliday:
    def test_tag_name_limit(self, conn):
        create_tag(conn, "t" * 50)
        with pytest.raises(ValidationError):
            create_tag(conn, "t" * 51)
        tag = create_tag(conn, "短い")
        with pytest.raises(ValidationError):
            update_tag(conn, tag.id, name="t" * 51)

    def test_status_label_limit(self, conn, statuses):
        create_status(conn, "s" * 50)
        with pytest.raises(ValidationError):
            create_status(conn, "s" * 51)
        status = create_status(conn, "別")
        with pytest.raises(ValidationError):
            update_status(conn, status.id, label="s" * 51)

    def test_holiday_name_limit_including_bulk_import(self, conn):
        upsert_holiday(conn, "2026-01-01", "元" * 100)
        with pytest.raises(ValidationError):
            upsert_holiday(conn, "2026-01-02", "元" * 101)
        with pytest.raises(ValidationError):
            bulk_upsert_holidays(conn, [("2026-02-01", "ok"), ("2026-02-02", "元" * 101)])


def test_error_message_is_translated(conn):
    from app import i18n

    i18n.set_language("en")
    try:
        with pytest.raises(ValidationError) as exc:
            create_tag(conn, "t" * 51)
        assert exc.value.localized() == "Please check your input (Name must be 1-50 characters)"
    finally:
        i18n.set_language("ja")
