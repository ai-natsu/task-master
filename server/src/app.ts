import express, { type NextFunction, type Request, type Response } from "express";
import cors from "cors";
import projectsRouter from "./routes/projects.js";
import tasksRouter from "./routes/tasks.js";
import tagsRouter from "./routes/tags.js";
import statsRouter from "./routes/stats.js";
import statusesRouter from "./routes/statuses.js";
import holidaysRouter from "./routes/holidays.js";
import { MSG, sendError } from "./errors.js";

export function createApp() {
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
