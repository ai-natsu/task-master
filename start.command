#!/bin/sh
# macOS: double-click this file in Finder to start TaskMaster (opens in Terminal).
# First time only: right-click -> Open (macOS asks for confirmation), or run: chmod +x start.command start.sh
cd "$(dirname "$0")" || exit 1
sh ./start.sh
status=$?
echo
echo "TaskMaster stopped. Press Enter to close this window."
read _
exit $status
