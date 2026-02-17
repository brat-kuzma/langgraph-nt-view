# LangGraph NT View — Frontend

Vue 3 + TypeScript + Vite фронтенд для управления проектами, тестами, артефактами и отчётами.

## Стек

- **Vue 3** (Composition API)
- **TypeScript**
- **Vite**
- **Vue Router**
- **Pinia**
- **Tailwind CSS**
- **Axios**

## Запуск

```bash
# Установка зависимостей
npm install

# Режим разработки (с hot reload)
npm run dev

# Сборка для продакшена
npm run build

# Предпросмотр сборки
npm run preview
```

Фронтенд по умолчанию работает на `http://localhost:5173`. API проксируется на `http://localhost:8000` — убедитесь, что бэкенд запущен.

## Структура

```
src/
├── api/           # API клиент
├── components/    # Vue компоненты
│   ├── project/   # Карточка проекта, форма
│   └── test/      # Карточка теста, форма
├── layouts/       # Layout
├── router/        # Vue Router
├── stores/        # Pinia stores
├── types/         # TypeScript типы
└── views/         # Страницы
```

## Функциональность

- **Проекты** — CRUD, настройки Grafana/K8s, LLM (тип, модель, API ключ)
- **Тесты** — создание, типы (поиск максимума, подтверждение, надёжность, деструктивный)
- **Артефакты** — загрузка, список, скачать всё (ZIP), удалить всё
- **Сбор данных** — Grafana (срезы дашборда), Kubernetes (логи и поды)
- **Отчёты** — просмотр/скачивание PDF и текста
- **Анализ** — запуск агента LangGraph
