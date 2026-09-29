import tempfile
from pathlib import Path

import pytest

from app.db.connection import connect


@pytest.fixture
def conn():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        c = connect(db_path)
        yield c
        c.close()


@pytest.fixture
def statuses(conn):
    """TODO(未完了)/DONE(完了)の2ステータスを投入する。"""
    with conn:
        conn.execute(
            'INSERT INTO "Status" (id, label, color, "order", isDone) VALUES '
            "('TODO', '未着手', '#64748b', 0, 0), "
            "('DONE', '完了', '#10b981', 1, 1)"
        )
    return ("TODO", "DONE")
