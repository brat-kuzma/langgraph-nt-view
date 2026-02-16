#!/usr/bin/env bash
# Остановить процесс на порту 8000 (uvicorn)
PORT="${1:-8000}"
PID=$(lsof -ti ":$PORT" 2>/dev/null)
if [ -z "$PID" ]; then
  echo "Порт $PORT свободен, процесс не найден."
  exit 0
fi
echo "Останавливаю процесс на порту $PORT (PID: $PID)"
kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
echo "Готово."
