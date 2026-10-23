import { join } from "node:path";
import express, { type NextFunction, type Request, type Response } from "express";
import cors from "cors";
import projectsRouter from "./routes/projects.js";
import tasksRouter from "./routes/tasks.js";
import tagsRouter from "./routes/tags.js";
import statsRouter from "./routes/stats.js";
import statusesRouter from "./routes/statuses.js";
import holidaysRouter from "./routes/holidays.js";
import { MSG, sendError } from "./errors.js";

export interface AppOptions {
  /** ビルド済みの画面（client/dist）のフォルダ。指定すると、API と同じサーバーから画面も配信する（本番用）。 */
  staticDir?: string;
}

export function createApp(options: AppOptions = {}) {
  const app = express();

  app.use(cors());
  app.use(express.json());

  app.use("/api/projects", projectsRouter);
  app.use("/api/tasks", tasksRouter);
  app.use("/api/tags", tagsRouter);
  app.use("/api/stats", statsRouter);
  app.use("/api/statuses", statusesRouter);
  app.use("/api/holidays", holidaysRouter);

  app.get("/api/health", (_req, res) => res.json({ ok: true }));

  // 本番：ビルド済みの画面を配信する。/api 以外のパス（/projects/xxx など）は、画面側のルーティングに任せるため index.html を返す
  if (options.staticDir) {
    const indexHtml = join(options.staticDir, "index.html");
    app.use(express.static(options.staticDir));
    app.get(/^\/(?!api\/).*/, (_req, res) => res.sendFile(indexHtml));
  }

  // 想定外のエラー（本文の JSON が不正、処理中の例外など）も、共通のエラー形式で返す
  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    if ((err as { type?: string }).type === "entity.parse.failed") {
      return sendError(res, 400, MSG.invalidInput);
    }
    console.error(err);
    sendError(res, 500, MSG.unexpected);
  });

  return app;
}
