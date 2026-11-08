#!/bin/bash
# ParkOS — Serverni to'xtatish

DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$DIR/.server.pid" ]; then
  PID=$(cat "$DIR/.server.pid")
  kill "$PID" 2>/dev/null
  rm "$DIR/.server.pid"
fi

# Portni ham tozalash
lsof -ti:8000 | xargs kill -9 2>/dev/null

osascript -e 'display notification "Server to'\''xtatildi." with title "ParkOS"'
