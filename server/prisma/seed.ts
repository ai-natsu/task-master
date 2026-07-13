import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const DEFAULT_STATUSES = [
  { id: "TODO", label: "未着手", color: "#64748b", order: 0, isDone: false },
  { id: "IN_PROGRESS", label: "進行中", color: "#6366f1", order: 1, isDone: false },
  { id: "DONE", label: "完了", color: "#10b981", order: 2, isDone: true },
  { id: "WITHDRAWN", label: "取下げ", color: "#94a3b8", order: 3, isDone: true },
];

async function main() {
  await prisma.taskTag.deleteMany();
  await prisma.task.deleteMany();
  await prisma.tag.deleteMany();
  await prisma.project.deleteMany();

  for (const s of DEFAULT_STATUSES) {
    await prisma.status.upsert({ where: { id: s.id }, update: {}, create: s });
  }

  const urgent = await prisma.tag.create({ data: { name: "urgent", color: "#ef4444" } });
  const design = await prisma.tag.create({ data: { name: "design", color: "#8b5cf6" } });
  const backend = await prisma.tag.create({ data: { name: "backend", color: "#0ea5e9" } });

  const website = await prisma.project.create({
    data: { name: "Webサイトリニューアル", color: "#6366f1", order: 0 },
  });
  const app = await prisma.project.create({
    data: { name: "モバイルアプリ開発", color: "#22c55e", order: 1 },
  });

  const design_task = await prisma.task.create({
    data: {
      title: "トップページのデザイン刷新",
      description: "新しいブランドガイドラインに沿ってトップページをデザインする",
      status: "IN_PROGRESS",
      priority: "HIGH",
      projectId: website.id,
      order: 0,
      dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
      tags: { create: [{ tagId: design.id }] },
    },
  });

  await prisma.task.create({
    data: {
      title: "ワイヤーフレーム作成",
      status: "DONE",
      priority: "MEDIUM",
      projectId: website.id,
      parentId: design_task.id,
      order: 0,
    },
  });
  await prisma.task.create({
    data: {
      title: "配色パターンの決定",
      status: "IN_PROGRESS",
      priority: "MEDIUM",
      projectId: website.id,
      parentId: design_task.id,
      order: 1,
      tags: { create: [{ tagId: design.id }] },
    },
  });

  const api_task = await prisma.task.create({
    data: {
      title: "APIエンドポイントの実装",
      description: "ユーザー認証とタスク管理のREST APIを実装",
      status: "TODO",
      priority: "URGENT",
      projectId: website.id,
      order: 1,
      dueDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
      tags: { create: [{ tagId: backend.id }, { tagId: urgent.id }] },
    },
  });
  await prisma.task.create({
    data: {
      title: "認証エンドポイント",
      status: "TODO",
      priority: "HIGH",
      projectId: website.id,
      parentId: api_task.id,
      order: 0,
    },
  });
  await prisma.task.create({
    data: {
      title: "タスクCRUDエンドポイント",
      status: "TODO",
      priority: "HIGH",
      projectId: website.id,
      parentId: api_task.id,
      order: 1,
    },
  });

  await prisma.task.create({
    data: {
      title: "SEO対策",
      status: "TODO",
      priority: "LOW",
      projectId: website.id,
      order: 2,
    },
  });

  const onboarding = await prisma.task.create({
    data: {
      title: "オンボーディングフロー設計",
      status: "TODO",
      priority: "MEDIUM",
      projectId: app.id,
      order: 0,
      dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
    },
  });
  await prisma.task.create({
    data: {
      title: "チュートリアル画面のワイヤーフレーム",
      status: "TODO",
      priority: "LOW",
      projectId: app.id,
      parentId: onboarding.id,
      order: 0,
    },
  });

  await prisma.task.create({
    data: {
      title: "プッシュ通知機能",
      status: "TODO",
      priority: "MEDIUM",
      projectId: app.id,
      order: 1,
      tags: { create: [{ tagId: backend.id }] },
    },
  });

  console.log("Seed data created.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
