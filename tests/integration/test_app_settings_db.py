from app.db.settings import get_setting, set_setting


def test_get_missing_key_returns_default(conn):
    assert get_setting(conn, "language") is None
    assert get_setting(conn, "language", "ja") == "ja"


def test_set_and_get_roundtrip(conn):
    set_setting(conn, "language", "en")
    assert get_setting(conn, "language") == "en"


def test_set_same_key_updates_value(conn):
    set_setting(conn, "language", "en")
    set_setting(conn, "language", "ja")
    assert get_setting(conn, "language") == "ja"
