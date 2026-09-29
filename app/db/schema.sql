-- TaskMaster データモデル定義（旧 server/prisma/schema.prisma の移植）
-- SQLite には BOOLEAN 型が無いため archived/isDone は INTEGER(0/1) で表現する。
-- updatedAt の自動更新は Prisma の @updatedAt と異なりトリガーではなく、
-- 各 UPDATE 文側で明示的に CURRENT_TIMESTAMP を渡す運用とする（app/db/*.py 参照）。

CREATE TABLE IF NOT EXISTS "Project" (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    color       TEXT NOT NULL DEFAULT '#6366f1',
    archived    INTEGER NOT NULL DEFAULT 0,
    "order"     INTEGER NOT NULL DEFAULT 0,
    createdAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS "Status" (
    id      TEXT PRIMARY KEY,
    label   TEXT NOT NULL,
    color   TEXT NOT NULL DEFAULT '#64748b',
    "order" INTEGER NOT NULL DEFAULT 0,
    isDone  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "Task" (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'TODO' REFERENCES "Status"(id) ON DELETE RESTRICT,
    priority    TEXT NOT NULL DEFAULT 'MEDIUM',
    startDate   TEXT,
    dueDate     TEXT,
    "order"     INTEGER NOT NULL DEFAULT 0,
    createdAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    projectId   TEXT NOT NULL REFERENCES "Project"(id) ON DELETE CASCADE,
    parentId    TEXT REFERENCES "Task"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_projectId ON "Task"(projectId);
CREATE INDEX IF NOT EXISTS idx_task_parentId  ON "Task"(parentId);
CREATE INDEX IF NOT EXISTS idx_task_status    ON "Task"(status);
CREATE INDEX IF NOT EXISTS idx_task_priority  ON "Task"(priority);
CREATE INDEX IF NOT EXISTS idx_task_dueDate   ON "Task"(dueDate);

CREATE TABLE IF NOT EXISTS "Tag" (
    id    TEXT PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#94a3b8'
);

CREATE TABLE IF NOT EXISTS "TaskTag" (
    taskId TEXT NOT NULL REFERENCES "Task"(id) ON DELETE CASCADE,
    tagId  TEXT NOT NULL REFERENCES "Tag"(id) ON DELETE CASCADE,
    PRIMARY KEY (taskId, tagId)
);

-- 祝日（ガントチャートでの色分け・設定画面での管理用）。日付は "YYYY-MM-DD"。
-- CSV一括登録は日付が一致する既存行を更新する仕様のため、date を一意制約にする。
CREATE TABLE IF NOT EXISTS "Holiday" (
    id   TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
