#!/usr/bin/env bash
# Запуск без --reload (для прода или когда не нужна перезагрузка при изменениях)
set -e
cd "$(dirname "$0")/.."
unset DATABASE_URL
. .venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
