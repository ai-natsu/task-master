"""簡易多言語対応。

日本語の原文そのものを辞書のキーとして使う方式。英語辞書
(app/locales/en.py)にキーが無ければ原文をそのまま返すため、
翻訳し忘れた文字列があってもアプリは壊れない（gettextのmsgidと同じ考え方）。
"""

from app.locales.en import TRANSLATIONS as _EN_TRANSLATIONS

LANGUAGES = {"ja": "日本語", "en": "English"}

_current_language = "ja"

_TABLES: dict[str, dict[str, str]] = {"en": _EN_TRANSLATIONS}


def get_language() -> str:
    return _current_language


def set_language(code: str) -> None:
    global _current_language
    if code not in LANGUAGES:
        raise ValueError(f"未対応の言語コードです: {code}")
    _current_language = code


def t(text: str) -> str:
    """現在の言語に翻訳する。未登録なら原文(日本語)をそのまま返す。"""
    table = _TABLES.get(_current_language)
    if table is None:
        return text
    return table.get(text, text)
