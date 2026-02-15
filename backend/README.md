# Backend — LangGraph NT View

Агент LangGraph для анализа результатов нагрузочного тестирования: Grafana, Kubernetes, артефакты (логи JVM, GC и т.д.), генерация отчётов (PDF + текст).

## Стек

- **FastAPI** — API
- **SQLite** по умолчанию / **PostgreSQL** по желанию
- **LangGraph** — агент анализа
- **LLM**: Ollama (qwen2.5vl:7b), GigaChat, OpenAI-совместимые
- **Grafana API**, **Kubernetes client**, **ReportLab** (PDF)

---

## Быстрый старт

### Первый раз (установка)

```bash
cd backend
./scripts/install.sh
```

Скрипт создаёт `.venv`, ставит зависимости и копирует `.env.example` в `.env`, если его нет.

### Запуск

```bash
cd backend
./scripts/run.sh
```

Откроется **http://localhost:8000**. Документация API: **http://localhost:8000/docs**.

Остановка: `Ctrl+C`.

### Скрипты (папка `scripts/`)

| Скрипт | Назначение |
|--------|------------|
| `install.sh` | Создать venv, установить зависимости, создать `.env` из примера |
| `run.sh` | Запуск с перезагрузкой при изменении кода (разработка) |
| `run-without-reload.sh` | Запуск без перезагрузки |

При запуске через скрипты используется `backend/.env` (в т.ч. SQLite), переменная `DATABASE_URL` из шелла не подставляется.

---

## Конфигурация (.env)

- **DATABASE_URL** — по умолчанию `sqlite:///./ntview.db` (файл в каталоге `backend/`). Для PostgreSQL: `postgresql+psycopg2://user:pass@host:5432/ntview`.
- **OLLAMA_BASE_URL** — для Ollama, по умолчанию `http://localhost:11434`.
- **STORAGE_PATH** — каталог для артефактов и отчётов (по умолчанию `storage`).

Таблицы создаются при первом старте приложения.

---

## Проверка работы

1. **http://localhost:8000/health** — ответ `{"status":"ok"}`.
2. **http://localhost:8000/docs** — Swagger UI.

Минимальный сценарий (без Grafana/K8s):

1. **POST /api/projects/** — тело: `{"name": "Тест", "llm_type": "ollama", "llm_model": "qwen2.5vl:7b"}`.
2. **POST /api/tests/** — тело: `{"project_id": 1, "test_type": "max_search"}`.
3. **POST /api/artifacts/test/1/upload** — form: `kind=custom_java_log`, `file` = любой .log/.txt.
4. **POST /api/tests/1/run-analysis** — нужна запущенная Ollama с моделью `qwen2.5vl:7b`.
5. **GET /api/reports/test/1**, **/api/reports/test/1/pdf** — отчёт.

---

## Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | /health | Проверка работы |
| GET | /docs | Swagger UI |
| POST | /api/projects/ | Создать проект |
| GET | /api/projects/ | Список проектов |
| POST | /api/tests/ | Создать тест |
| POST | /api/tests/{id}/run-analysis | Запустить анализ (агент) |
| POST | /api/collect/test/{id}/grafana | Собрать срезы Grafana |
| POST | /api/collect/test/{id}/kubernetes | Собрать поды и логи K8s |
| POST | /api/artifacts/test/{id}/upload | Загрузить артефакт |
| GET | /api/artifacts/download-all/{id} | Скачать артефакты теста (ZIP) |
| GET | /api/reports/test/{id} | Отчёт по тесту |
| GET | /api/reports/test/{id}/text | Текст отчёта |
| GET | /api/reports/test/{id}/pdf | PDF отчёта |

Типы тестов: `max_search`, `max_confirmation`, `reliability`, `destructive`.

---

## Запуск без скриптов

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# при необходимости отредактировать .env

# Чтобы использовался SQLite из .env (если в шелле задан DATABASE_URL на postgres):
unset DATABASE_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
