@echo off
rem TaskMaster (V2): run from source. Creates a virtual environment and installs the app the first time.
rem Double-click this file, or run it in a terminal. Close the TaskMaster window to stop.
rem Set TASKMASTER_CHECK_ONLY=1 to only prepare (virtual environment and install) without opening the app.
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python was not found.
  echo         Install Python 3.11 or later from https://www.python.org/downloads/
  echo         ^(check "Add python.exe to PATH" in the installer^), reopen this window, and run start.cmd again.
  pause
  exit /b 1
)

if not exist .venv\Scripts\python.exe (
  echo [1/3] Creating the virtual environment ^(first time only^)...
  %PY% -m venv .venv || goto :error
)

if not exist .venv\.installed (
  echo [2/3] Installing TaskMaster and its libraries ^(first time only, takes a minute^)...
  call .venv\Scripts\python.exe -m pip install --upgrade pip >nul
  call .venv\Scripts\python.exe -m pip install -e . || goto :error
  echo done> .venv\.installed
)

if defined TASKMASTER_CHECK_ONLY (
  echo [3/3] Ready ^(check only, the app was not started^).
  goto :eof
)

echo [3/3] Starting TaskMaster...
.venv\Scripts\python.exe -m app.main
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo [ERROR] Failed. Please check the messages above.
pause
exit /b 1
