#!/usr/bin/env bash
# Установка зависимостей и окружения (из корня backend/)
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан .env из .env.example — при необходимости отредактируйте."
fi
echo "Готово. Запуск: ./scripts/run.sh"
