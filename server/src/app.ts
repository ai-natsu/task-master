import express from "express";
import cors from "cors";
import projectsRouter from "./routes/projects.js";
import tasksRouter from "./routes/tasks.js";
import tagsRouter from "./routes/tags.js";
import statsRouter from "./routes/stats.js";
import statusesRouter from "./routes/statuses.js";
import holidaysRouter from "./routes/holidays.js";

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

  return app;
}
