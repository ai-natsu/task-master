import "dotenv/config";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createApp } from "./app.js";

// ビルド済みの画面（client/dist）があれば、同じサーバーから配信する（server/dist から見て ../../client/dist）
const clientDist = resolve(dirname(fileURLToPath(import.meta.url)), "../../client/dist");
const staticDir = existsSync(resolve(clientDist, "index.html")) ? clientDist : undefined;

const app = createApp({ staticDir });
const port = process.env.PORT ?? 3001;

app.listen(port, () => {
  console.log(`Server listening on http://localhost:${port}`);
  if (staticDir) console.log(`画面も配信しています: http://localhost:${port}`);
});
