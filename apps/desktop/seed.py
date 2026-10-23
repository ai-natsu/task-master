"""サンプルデータ投入（旧 server/prisma/seed.ts の移植）。

実行前に既存データを全削除する破壊的スクリプト。
"""

import datetime

from app.db.connection import DEFAULT_STATUSES, connect
from app.db.projects import create_project
from app.db.tags import create_tag
from app.db.tasks import create_task


def _days_from_now(days: int) -> str:
    dt = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=days)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def main() -> None:
    conn = connect()
    with conn:
        conn.execute('DELETE FROM "TaskTag"')
        conn.execute('DELETE FROM "Task"')
        conn.execute('DELETE FROM "Tag"')
        conn.execute('DELETE FROM "Project"')
        for status_id, label, color, order, is_done in DEFAULT_STATUSES:
            conn.execute(
                """
                INSERT INTO "Status" (id, label, color, "order", isDone)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (status_id, label, color, order, is_done),
            )

    urgent = create_tag(conn, "urgent", "#ef4444")
    design = create_tag(conn, "design", "#8b5cf6")
    backend = create_tag(conn, "backend", "#0ea5e9")

    website = create_project(conn, "Webサイトリニューアル", color="#6366f1")
    app_project = create_project(conn, "モバイルアプリ開発", color="#22c55e")

    design_task = create_task(
        conn,
        title="トップページのデザイン刷新",
        project_id=website.id,
        description="新しいブランドガイドラインに沿ってトップページをデザインする",
        status="IN_PROGRESS",
        priority="HIGH",
        due_date=_days_from_now(2),
        tag_ids=[design.id],
    )
    create_task(
        conn, title="ワイヤーフレーム作成", project_id=website.id,
        parent_id=design_task.id, status="DONE", priority="MEDIUM",
    )
    create_task(
        conn, title="配色パターンの決定", project_id=website.id,
        parent_id=design_task.id, status="IN_PROGRESS", priority="MEDIUM",
        tag_ids=[design.id],
    )

    api_task = create_task(
        conn,
        title="APIエンドポイントの実装",
        project_id=website.id,
        description="ユーザー認証とタスク管理のREST APIを実装",
        status="TODO",
        priority="URGENT",
        due_date=_days_from_now(-1),
        tag_ids=[backend.id, urgent.id],
    )
    create_task(
        conn, title="認証エンドポイント", project_id=website.id,
        parent_id=api_task.id, status="TODO", priority="HIGH",
    )
    create_task(
        conn, title="タスクCRUDエンドポイント", project_id=website.id,
        parent_id=api_task.id, status="TODO", priority="HIGH",
    )

    create_task(conn, title="SEO対策", project_id=website.id, status="TODO", priority="LOW")

    onboarding = create_task(
        conn, title="オンボーディングフロー設計", project_id=app_project.id,
        status="TODO", priority="MEDIUM", due_date=_days_from_now(5),
    )
    create_task(
        conn, title="チュートリアル画面のワイヤーフレーム", project_id=app_project.id,
        parent_id=onboarding.id, status="TODO", priority="LOW",
    )

    create_task(
        conn, title="プッシュ通知機能", project_id=app_project.id,
        status="TODO", priority="MEDIUM", tag_ids=[backend.id],
    )

    print("Seed data created.")


if __name__ == "__main__":
    main()
