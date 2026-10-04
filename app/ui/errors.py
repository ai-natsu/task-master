"""エラー表示の共通処理（V1/V2 共通の方針：docs/BASIC_DESIGN.md §7.2）。

- 入力フォーム（タスク・プロジェクト）の保存失敗 → モーダルを閉じず、ボタンの上に赤字で表示
- 設定画面の操作失敗 → 操作した節の直下に赤字で表示
- 一覧・ビュー上の操作失敗、想定外のエラー → エラーダイアログ（show_error）
"""

from tkinter import messagebox

from app.db.errors import UNEXPECTED_ERROR, AppError
from app.i18n import t


def error_message(exc: BaseException) -> str:
    """画面に出すメッセージ。業務例外は現在の言語に翻訳し、それ以外は想定外のエラーの共通文言にする。"""
    if isinstance(exc, AppError):
        return exc.localized()
    return t(UNEXPECTED_ERROR)


def show_error(parent, exc: BaseException) -> None:
    messagebox.showerror(t("エラー"), error_message(exc), parent=parent)


def required_message(field: str) -> str:
    """必須項目が未入力のときの共通メッセージ。field は日本語の項目名（「名前」など）。"""
    return t("{field}を入力してください").format(field=t(field))
