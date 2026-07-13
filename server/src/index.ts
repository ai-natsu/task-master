import "dotenv/config";
import express from "express";
import cors from "cors";
import projectsRouter from "./routes/projects.js";
import tasksRouter from "./routes/tasks.js";
import tagsRouter from "./routes/tags.js";
import statsRouter from "./routes/stats.js";
import statusesRouter from "./routes/statuses.js";

const app = express();
const port = process.env.PORT ?? 3001;

app.use(cors());
app.use(express.json());

app.use("/api/projects", projectsRouter);
app.use("/api/tasks", tasksRouter);
app.use("/api/tags", tagsRouter);
app.use("/api/stats", statsRouter);
app.use("/api/statuses", statusesRouter);

app.get("/api/health", (_req, res) => res.json({ ok: true }));

app.listen(port, () => {
  console.log(`Server listening on http://localhost:${port}`);
});
