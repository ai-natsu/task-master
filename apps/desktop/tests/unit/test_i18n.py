import pytest

from app import i18n


@pytest.fixture(autouse=True)
def _reset_language():
    yield
    i18n.set_language("ja")


def test_defaults_to_japanese():
    assert i18n.get_language() == "ja"


def test_returns_original_text_when_language_is_japanese():
    assert i18n.t("ダッシュボード") == "ダッシュボード"


def test_unknown_key_falls_back_to_original_text():
    i18n.set_language("en")
    assert i18n.t("そんな文字列は無い") == "そんな文字列は無い"


def test_translates_known_key_when_language_is_english(monkeypatch):
    monkeypatch.setitem(i18n._EN_TRANSLATIONS, "ダッシュボード", "Dashboard")
    i18n.set_language("en")
    assert i18n.t("ダッシュボード") == "Dashboard"


def test_set_language_rejects_unknown_code():
    with pytest.raises(ValueError):
        i18n.set_language("fr")

