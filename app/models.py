"""dataclass によるドメインモデル（旧 Prisma モデルの移植）。

sqlite3.Row からの変換は各 db/*.py モジュール側で行う。
"""

from dataclasses import dataclass, field


@dataclass
class Status:
    id: str
    label: str
    color: str = "#64748b"
    order: int = 0
    is_done: bool = False


@dataclass
class Tag:
    id: str
    name: str
    color: str = "#94a3b8"


@dataclass
class Task:
    id: str
    title: str
    project_id: str
    description: str | None = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    start_date: str | None = None
    due_date: str | None = None
    order: int = 0
    created_at: str = ""
    updated_at: str = ""
    parent_id: str | None = None
    tags: list[Tag] = field(default_factory=list)


@dataclass
class Project:
    id: str
    name: str
    description: str | None = None
    color: str = "#6366f1"
    archived: bool = False
    order: int = 0
    created_at: str = ""
    updated_at: str = ""
    task_count: int = 0


@dataclass
class Holiday:
    id: str
    date: str  # "YYYY-MM-DD"
    name: str
