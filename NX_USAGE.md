# Использование NX в проекте langgraph-nt-view

## Гибридный подход

Проект использует NX как task runner с кешированием, сохраняя текущую структуру (backend/ и frontend/ остаются на месте).

## Установка

NX уже установлен в корне проекта. Если нужно переустановить:

```bash
npm install
```

## Основные команды

### Просмотр всех проектов
```bash
npx nx run-many --target=build --all --dry-run
```

### Backend команды

#### Установка зависимостей
```bash
npx nx run backend:install
```

#### Запуск в dev режиме
```bash
npx nx run backend:serve
```

#### Сборка (проверка зависимостей)
```bash
npx nx run backend:build
```

#### Тесты
```bash
npx nx run backend:test
```

#### Линтинг
```bash
npx nx run backend:lint
```

### Frontend команды

#### Установка зависимостей
```bash
npx nx run frontend:install
```

#### Запуск в dev режиме
```bash
npx nx run frontend:serve
```

#### Сборка
```bash
npx nx run frontend:build
```

#### Preview (после сборки)
```bash
npx nx run frontend:preview
```

#### Тесты
```bash
npx nx run frontend:test
```

#### Линтинг
```bash
npx nx run frontend:lint
```

## Параллельное выполнение

Запустить несколько задач параллельно:

```bash
# Сборка всех проектов
npx nx run-many --target=build --all

# Установка зависимостей для всех проектов
npx nx run-many --target=install --all

# Запуск тестов для всех проектов
npx nx run-many --target=test --all
```

## Кеширование

NX автоматически кеширует результаты задач. При повторном запуске, если входные данные не изменились, задача пропускается.

### Очистка кеша
```bash
npx nx reset
```

### Просмотр кеша
```bash
# Показать информацию о кеше
npx nx show project backend --json
```

## Зависимости между задачами

Задачи автоматически учитывают зависимости:
- `backend:build` зависит от `backend:install`
- `frontend:build` зависит от `frontend:install`

## Примеры использования

### Разработка (запуск обоих проектов)

В двух терминалах:

```bash
# Терминал 1: Backend
npx nx run backend:serve

# Терминал 2: Frontend
npx nx run frontend:serve
```

### CI/CD сценарий

```bash
# Установка зависимостей для всех проектов
npx nx run-many --target=install --all

# Сборка всех проектов
npx nx run-many --target=build --all

# Запуск тестов
npx nx run-many --target=test --all
```

### Только изменённые проекты (affected)

Если настроен git:

```bash
# Сборка только изменённых проектов
npx nx affected --target=build

# Тесты только для изменённых проектов
npx nx affected --target=test
```

## Структура конфигурации

- `nx.json` — глобальная конфигурация NX
- `backend/project.json` — конфигурация backend проекта
- `frontend/project.json` — конфигурация frontend проекта

## Преимущества гибридного подхода

✅ **Кеширование** — повторные сборки выполняются мгновенно  
✅ **Параллельное выполнение** — задачи могут выполняться одновременно  
✅ **Единые команды** — один интерфейс для всех проектов  
✅ **Минимальные изменения** — структура проекта не изменена  
✅ **Граф зависимостей** — автоматическое определение порядка выполнения

## Миграция на полный NX (опционально)

Если в будущем понадобится полная миграция на NX с плагинами:
1. Установить плагины: `@nx/vue`, `@nx/node`
2. Переместить проекты в `apps/`
3. Создать shared libraries в `libs/`
4. Настроить импорты между библиотеками

См. `NX_STRUCTURE_ANALYSIS.md` для деталей.
