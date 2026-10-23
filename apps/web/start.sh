#!/bin/sh
# TaskMaster: first-time setup (only when needed), build (only when needed), then start.
# Open http://localhost:3001 in your browser. Press Ctrl+C to stop.
# Set TASKMASTER_NO_BROWSER=1 to skip opening the browser automatically.
set -e
cd "$(dirname "$0")"

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] Node.js was not found. Install Node.js LTS from https://nodejs.org/ and run ./start.sh again."
  exit 1
fi

if [ ! -d node_modules ]; then
  echo "[1/4] Installing dependencies... (first time only, takes a few minutes)"
  npm install
fi

[ -f server/.env ] || cp server/.env.example server/.env

echo "[2/4] Preparing the database..."
(cd server && npx prisma migrate deploy)

if [ ! -f server/dist/index.js ] || [ ! -f client/dist/index.html ]; then
  echo "[3/4] Building... (first time only)"
  npm run build
fi

echo "[4/4] Starting TaskMaster at http://localhost:3001  (Ctrl+C to stop)"
if [ -z "$TASKMASTER_NO_BROWSER" ]; then
  (sleep 3; (open http://localhost:3001 || xdg-open http://localhost:3001) >/dev/null 2>&1) &
fi
exec npm start
