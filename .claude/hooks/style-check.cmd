@echo off
REM PostToolUse フックのラッパー（Windows）。dev.cmd と同方式で Node の PATH を
REM 通してから style-check-file.js を実行する。stdin（フックの JSON）は素通しする。
set PATH=C:\Program Files\nodejs;%PATH%
node "%~dp0style-check-file.js"
