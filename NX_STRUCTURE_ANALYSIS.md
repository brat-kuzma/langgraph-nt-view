# Анализ структуры проекта langgraph-nt-view (NX MCP)

## Текущая структура проекта

### Общая информация
- **Тип**: Монорепозиторий без NX
- **Backend**: Python/FastAPI (26 Python файлов)
- **Frontend**: Vue 3 + Vite + TypeScript (16 файлов .ts/.vue)
- **Архитектура**: Раздельные приложения (backend/ и frontend/)

### Структура директорий

```
langgraph-nt-view/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph агент (graph, nodes, state, llm_factory)
│   │   ├── api/            # FastAPI routes (projects, tests, artifacts, reports)
│   │   ├── db/             # SQLAlchemy models, database setup
│   │   ├── services/       # Business logic (analysis_runner, artifacts, grafana, kubernetes, report_generator)
│   │   ├── config.py       # Settings (Pydantic)
│   │   └── main.py         # FastAPI app entry point
│   ├── scripts/            # Shell scripts (install, run, stop)
│   ├── storage/            # Artifacts, reports, grafana snapshots
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API client (axios)
│   │   ├── components/     # Vue components (project, test)
│   │   ├── stores/         # Pinia stores (projects, tests)
│   │   ├── views/          # Vue Router views
│   │   └── types/          # TypeScript types
│   ├── public/
│   └── package.json
└── .gitignore
```

## Анализ по рекомендациям NX

### ✅ Что работает хорошо

1. **Чёткое разделение**: Backend и frontend изолированы
2. **Модульная структура**: Backend разделён на логические модули (agent, api, services, db)
3. **Типизация**: TypeScript во frontend, type hints в Python
4. **Скрипты автоматизации**: Удобные shell-скрипты для разработки

### ⚠️ Проблемы текущей структуры

1. **Нет единой системы сборки**: Backend и frontend управляются отдельно
2. **Нет зависимостей между проектами**: Нет явного графа зависимостей
3. **Нет кеширования**: Каждая сборка выполняется с нуля
4. **Нет параллельного выполнения**: Задачи не могут выполняться параллельно
5. **Нет shared libraries**: Общие типы/утилиты не переиспользуются
6. **Нет тестов на уровне workspace**: Нет единой команды для запуска всех тестов

## Рекомендации по миграции на NX

### Вариант 1: Полная миграция на NX (рекомендуется для роста)

#### Преимущества
- ✅ Кеширование сборок и тестов
- ✅ Параллельное выполнение задач
- ✅ Граф зависимостей между проектами
- ✅ Единые команды для всего workspace
- ✅ Поддержка shared libraries
- ✅ Интеграция с CI/CD

#### Структура после миграции

```
langgraph-nt-view/
├── apps/
│   ├── backend/            # FastAPI приложение
│   └── frontend/           # Vue приложение
├── libs/
│   ├── shared/
│   │   ├── types/          # Общие TypeScript типы (API contracts)
│   │   └── api-client/     # Общий API client (можно использовать в обоих проектах)
│   ├── backend/
│   │   ├── agent/          # LangGraph агент (отдельная библиотека)
│   │   ├── services/       # Business logic libraries
│   │   └── db/             # Database models
│   └── frontend/
│       ├── ui/              # Shared UI components
│       └── stores/           # Shared Pinia stores
├── nx.json
├── package.json
└── tsconfig.base.json
```

#### Плагины NX для использования

1. **[@nx/vue]** — для Vue frontend
   - Генерация компонентов, библиотек
   - Интеграция с Vitest, Cypress, Storybook

2. **[@nx/node]** — для Python backend (через executors)
   - Запуск Python скриптов
   - Управление зависимостями (через custom executors)

3. **[@nx/js]** — для TypeScript библиотек
   - Общие типы и утилиты
   - Shared API client

4. **[@nx/vite]** — для сборки Vue приложения
   - Vite конфигурация
   - Dev server, build, preview

#### Команды после миграции

```bash
# Запуск всех проектов в dev режиме
nx run-many --target=serve --all

# Сборка всех проектов
nx run-many --target=build --all

# Запуск тестов для изменённых проектов
nx affected:test

# Просмотр графа зависимостей
nx graph
```

### Вариант 2: Гибридный подход (минимальные изменения)

Оставить текущую структуру, но добавить NX для:
- Управления задачами (task runner)
- Кеширования результатов
- Параллельного выполнения

#### Структура

```
langgraph-nt-view/
├── backend/                 # Остаётся как есть
├── frontend/                # Остаётся как есть
├── nx.json                  # Конфигурация NX
└── package.json             # Root package.json с NX
```

#### nx.json конфигурация

```json
{
  "tasksRunnerOptions": {
    "default": {
      "runner": "nx/tasks-runners/default",
      "options": {
        "cacheableOperations": ["build", "test", "lint"]
      }
    }
  },
  "targetDefaults": {
    "build": {
      "cache": true
    },
    "test": {
      "cache": true
    }
  },
  "projects": {
    "backend": {
      "targets": {
        "serve": {
          "executor": "nx:run-commands",
          "options": {
            "command": "cd backend && ./scripts/run.sh"
          }
        },
        "build": {
          "executor": "nx:run-commands",
          "options": {
            "command": "cd backend && pip install -r requirements.txt"
          }
        }
      }
    },
    "frontend": {
      "targets": {
        "serve": {
          "executor": "@nx/vite:dev-server",
          "options": {
            "buildTarget": "frontend:build"
          }
        },
        "build": {
          "executor": "@nx/vite:build"
        }
      }
    }
  }
}
```

## План миграции (если выбран вариант 1)

### Этап 1: Инициализация NX
```bash
npx nx@latest init
# Выбрать: Integrated monorepo
```

### Этап 2: Импорт существующих проектов
```bash
# Импорт frontend (Vue)
nx g @nx/vue:application frontend --directory=apps/frontend

# Импорт backend (Node executor для Python)
nx g @nx/node:application backend --directory=apps/backend
```

### Этап 3: Создание shared libraries
```bash
# Общие типы API
nx g @nx/js:library shared-types --directory=libs/shared/types

# API client
nx g @nx/js:library api-client --directory=libs/shared/api-client
```

### Этап 4: Настройка зависимостей
- Frontend зависит от `shared-types` и `api-client`
- Backend может использовать общие типы через генерацию из OpenAPI схемы

### Этап 5: Миграция кода
- Переместить код из `backend/app` в `apps/backend/src`
- Переместить код из `frontend/src` в `apps/frontend/src`
- Настроить импорты между библиотеками

## Рекомендации по плагинам NX

### Для Vue frontend
- **@nx/vue** — основной плагин
- **@nx/vite** — сборка через Vite
- **@nx/eslint-plugin** — линтинг
- **@nx/jest** или **@nx/vitest** — тестирование

### Для Python backend
- **@nx/node** — базовый плагин для Node-подобных проектов
- Custom executors для Python:
  - `python:run` — запуск Python скриптов
  - `python:test` — запуск pytest
  - `python:lint` — запуск ruff/mypy

### Общие плагины
- **@nx/eslint-plugin** — enforce module boundaries
- **@nx/dependency-graph** — визуализация зависимостей

## Выводы

### Текущее состояние
Проект имеет хорошую модульную структуру, но не использует преимущества монорепозитория:
- Нет кеширования
- Нет параллельного выполнения
- Нет явного графа зависимостей

### Рекомендация
**Для текущего размера проекта (26 Python файлов, 16 TS/Vue файлов)**: 
- Гибридный подход (Вариант 2) достаточен
- NX как task runner с кешированием
- Минимальные изменения в структуре

**Для роста проекта (добавление новых приложений/библиотек)**:
- Полная миграция на NX (Вариант 1)
- Выделение shared libraries
- Использование графа зависимостей

### Следующие шаги
1. Решить: гибридный подход или полная миграция
2. Если гибридный: добавить `nx.json` и настроить задачи
3. Если полная миграция: следовать плану миграции выше
4. Настроить CI/CD с использованием NX affected commands
