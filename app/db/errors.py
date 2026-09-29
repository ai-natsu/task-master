"""データ層で送出する業務例外。UI 層はこれを捕まえてダイアログ表示する。"""


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    pass


class CycleError(Exception):
    pass
