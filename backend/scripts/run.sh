#!/usr/bin/env bash
# Запуск backend (из корня backend/ или из scripts/)
set -e
cd "$(dirname "$0")/.."
if [ ! -d ".venv" ]; then
  echo "Создайте venv: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
# Убираем DATABASE_URL из окружения — приложение возьмёт значение из backend/.env (там SQLite по умолчанию)
unset DATABASE_URL
. .venv/bin/activate
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
