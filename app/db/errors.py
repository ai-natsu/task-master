"""データ層で送出する業務例外。

メッセージは V1/V2 共通の日本語（docs/BASIC_DESIGN.md §7.2）。パラメータ付きのものは
テンプレート（`{count}` など）と値を分けて持ち、画面側が現在の言語に翻訳して表示する
（`localized()`）。UI 層はこれを捕まえて、フォームの中・設定画面の節の下・ダイアログに表示する。
"""


class AppError(Exception):
    def __init__(self, message: str, **params: object):
        self.template = message
        self.params = params
        super().__init__(message.format(**params) if params else message)

    def localized(self) -> str:
        """現在の表示言語に翻訳したメッセージ。"""
        from app.i18n import t

        text = t(self.template)
        return text.format(**self.params) if self.params else text


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass


class ConflictError(AppError):
    pass


class CycleError(AppError):
    pass


# 想定外のエラー（上記以外の例外）の共通メッセージ
UNEXPECTED_ERROR = "予期しないエラーが発生しました。もう一度お試しください"
