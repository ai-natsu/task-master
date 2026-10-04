import pytest

from app import i18n
from app.db.errors import UNEXPECTED_ERROR, ConflictError, NotFoundError, ValidationError
from app.locales.en import TRANSLATIONS

# V1/V2 共通のエラーメッセージ（docs/BASIC_DESIGN.md §7.2）。日本語と英語の対応を固定する。
COMMON_MESSAGES = {
    "プロジェクトが見つかりません": "Project not found",
    "タスクが見つかりません": "Task not found",
    "ステータスが見つかりません": "Status not found",
    "タグが見つかりません": "Tag not found",
    "祝日が見つかりません": "Holiday not found",
    "親タスクが見つかりません": "Parent task not found",
    "指定のステータスが存在しません": "Invalid status",
    "ステータスが1件もありません": "No statuses defined",
    "CSVの文字コードを判定できませんでした": (
        "Could not determine the CSV file's character encoding."
    ),
    "タグが既に存在します": "Tag already exists",
    "このステータスは {count} 件のタスクで使用中のため削除できません": (
        "This status is used by {count} tasks and cannot be deleted"
    ),
    "最後のステータスは削除できません": "The last status cannot be deleted",
    "タスクを自分自身またはその配下には移動できません": (
        "A task cannot be moved under itself or its own subtasks"
    ),
    UNEXPECTED_ERROR: "An unexpected error occurred. Please try again.",
}


@pytest.fixture(autouse=True)
def _restore_language():
    yield
    i18n.set_language("ja")


@pytest.mark.parametrize(("ja", "en"), COMMON_MESSAGES.items())
def test_common_messages_have_the_agreed_english(ja, en):
    assert TRANSLATIONS[ja] == en


def test_plain_message_is_the_japanese_text_and_translates():
    exc = NotFoundError("タスクが見つかりません")
    assert str(exc) == "タスクが見つかりません"
    assert exc.localized() == "タスクが見つかりません"
    i18n.set_language("en")
    assert exc.localized() == "Task not found"


def test_parameterized_message_formats_and_translates():
    exc = ConflictError("このステータスは {count} 件のタスクで使用中のため削除できません", count=3)
    assert str(exc) == "このステータスは 3 件のタスクで使用中のため削除できません"
    i18n.set_language("en")
    assert exc.localized() == "This status is used by 3 tasks and cannot be deleted"


def test_all_business_errors_share_the_base_class():
    from app.db.errors import AppError, CycleError

    for cls in (NotFoundError, ValidationError, ConflictError, CycleError):
        assert issubclass(cls, AppError)


def test_required_message_ja_and_en():
    from app import i18n
    from app.ui.errors import required_message

    i18n.set_language("ja")
    assert required_message("タイトル") == "タイトルを入力してください"
    i18n.set_language("en")
    try:
        assert required_message("タイトル") == "Title is required."
        assert required_message("名前") == "Name is required."
    finally:
        i18n.set_language("ja")
