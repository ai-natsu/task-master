@echo off
rem TaskMaster: first-time setup (only when needed), build (only when needed), then start.
rem Open http://localhost:3001 in your browser. Close this window (or press Ctrl+C) to stop.
rem Set TASKMASTER_NO_BROWSER=1 to skip opening the browser automatically.
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found.
  echo         Install Node.js LTS from https://nodejs.org/ , reopen this window, and run start.cmd again.
  pause
  exit /b 1
)

if not exist node_modules (
  echo [1/4] Installing dependencies... ^(first time only, takes a few minutes^)
  call npm install || goto :error
)

if not exist server\.env copy server\.env.example server\.env >nul

echo [2/4] Preparing the database...
pushd server
call npx prisma migrate deploy
if errorlevel 1 ( popd & goto :error )
popd

if not exist server\dist\index.js goto :build
if not exist client\dist\index.html goto :build
goto :run

:build
echo [3/4] Building... ^(first time only, or after "npm run build" removed the output^)
call npm run build || goto :error

:run
echo [4/4] Starting TaskMaster at http://localhost:3001  ^(close this window to stop^)
if not defined TASKMASTER_NO_BROWSER start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:3001"
call npm start
goto :eof

:error
echo.
echo [ERROR] Failed. Please check the messages above.
pause
exit /b 1
