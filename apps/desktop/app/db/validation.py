"""入力値の検査（文字数の上限・必須）。違反したら ValidationError を送出する。

画面の入力欄にも同じ上限を設定している（app/ui/widgets/limits.py）が、データ層でも検査して、
画面を通らない経路（CSV の取り込みなど）でも仕様を守る。V1 は API の zod スキーマが同じ役割。
"""

from app.constants import LIMITS
from app.db.errors import ValidationError


def check_text(value: str | None, field: str, key: str, *, required: bool = True) -> None:
    """value の文字数を検査する。field は日本語の項目名（「名前」など）、key は LIMITS のキー。

    required=True なら 1 文字以上が必要。None は「指定なし」として、検査しない。
    """
    if value is None:
        return
    from app.i18n import t

    limit = LIMITS[key]
    if required and len(value) == 0:
        raise ValidationError(
            "入力内容を確認してください（{field}は1〜{max}文字）", field=t(field), max=limit
        )
    if len(value) > limit:
        if required:
            raise ValidationError(
                "入力内容を確認してください（{field}は1〜{max}文字）", field=t(field), max=limit
            )
        raise ValidationError(
            "入力内容を確認してください（{field}は{max}文字以内）", field=t(field), max=limit
        )
