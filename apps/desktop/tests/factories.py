"""テスト用の Task ファクトリ（旧 client/src/test/factories.ts の移植）。"""

from itertools import count

from app.models import Task

_seq = count(1)


def make_task(**overrides) -> Task:
    n = next(_seq)
    defaults = dict(
        id=f"t{n}",
        title=f"Task {n}",
        description=None,
        status="TODO",
        priority="MEDIUM",
        start_date=None,
        due_date=None,
        order=0,
        project_id="p1",
        parent_id=None,
        created_at="2026-01-01T00:00:00.000Z",
        updated_at="2026-01-01T00:00:00.000Z",
        tags=[],
    )
    defaults.update(overrides)
    return Task(**defaults)
