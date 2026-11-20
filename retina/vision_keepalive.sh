#!/usr/bin/env bash
# vision_keepalive.sh — start vision_watch.py if it isn't running.
# Idempotent: safe to run every 5 minutes from cron. Never starts a second copy.
set -euo pipefail

SCRIPT="$HOME/workspace/fly-brain/retina/vision_watch.py"
LOG="$HOME/workspace/fly-brain/retina/_work/vision_watch.log"

if pgrep -f "[v]ision_watch.py" > /dev/null 2>&1; then
    exit 0  # already watching
fi

export PYTHONPATH="$HOME/workspace/.pydeps${PYTHONPATH:+:$PYTHONPATH}"
cd "$HOME/workspace/fly-brain/retina"
# setsid detaches; nohup guards HUP. stdout -> /dev/null (log() already writes
# the file directly; redirecting stdout there too would double every line).
# stderr stays on the log for import-time tracebacks. Do NOT kill this
# launcher's session — process.kill tears down the whole tree including the
# detached watcher.
setsid nohup python3 "$SCRIPT" > /dev/null 2>> "$LOG" < /dev/null &
echo "vision_watch started (pid $!)"
