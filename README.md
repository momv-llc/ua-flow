# UA FLOW — MVP

Рабочий минимальный продукт по ТЗ: FastAPI backend + React (Vite) frontend + PostgreSQL.
Бэкенд реализует модули Core/Docs/Support/Integration/Admin/Analytics c JWT и 2FA.
Запуск через Docker Compose. Карта выполнения требований находится в [docs/roadmap.md](docs/roadmap.md).

## Быстрый старт

```bash
docker compose up --build
```

- Backend API (Swagger): http://localhost:8000/api/docs
- Frontend UI:        http://localhost:5173

### Основные REST-модули

- `/api/v1/auth` — регистрация, вход, refresh-токены, 2FA (TOTP).
- `/api/v1/projects` — команды, проекты, спринты, эпики.
- `/api/v1/tasks` — Kanban/Scrum задачи, комментарии, отчёты.
- `/api/v1/docs` — вики-документы с версионностью и подписями (КЕП).
- `/api/v1/support` — service desk, SLA, комментарии, назначения.
- `/api/v1/integrations` — Integration Hub (1C, Medoc, SPI, Diia, Prozorro, Webhooks) с Celery-очередью и песочницами.
- `/api/v1/admin` — управление пользователями, настройками, аудитом.
- `/api/v1/analytics` — метрики, тепловые карты тикетов, загрузка.

## Дефолтные креды

После регистрации через UI/или POST /api/v1/auth/register — войдите в систему.
Роли: `admin`, `user`. По умолчанию создаются пользователи с ролью `user`.

## Переменные окружения (пример)

Смотри `.env.example`. Для локального docker-compose значения уже прописаны.

> ℹ️ Если переменная `DATABASE_URL` не задана, backend автоматически
> использует локальную базу SQLite (`uaflow.db`). Это позволяет запустить
> API без внешнего PostgreSQL. Для продакшна обязательно укажите
> `DATABASE_URL` со строкой подключения к PostgreSQL.

## Очереди интеграций

- Redis поднимается автоматически (`redis` сервис в `docker-compose.yml`).
- Celery-воркер запускается отдельным сервисом `worker` (команда `celery -A backend.celery_app.celery_app worker`).
- Настройки брокера и результата настраиваются переменными `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`. Для локальной разработки включён eager-режим (задачи выполняются синхронно при отсутствии Redis).
- Подробные спецификации обмена и песочницы описаны в [docs/integrations/](docs/integrations/README.md).

## Локализация UI

Фронтенд использует i18next и поддерживает три языка: українська, English, русский. Переключатель языка доступен в шапке интерфейса и сохраняется в `localStorage`.

## Проверка сборки в Ubuntu Docker

Для быстрой проверки совместимости зависимостей с чистым образом Ubuntu 24.04 выполните:

```bash
./scripts/test_ubuntu_docker.sh
```

Скрипт поднимет одноразовый контейнер `ubuntu:24.04`, установит Python и Node.js, соберёт фронтенд и выполнит компиляцию бэкенда. Подробнее — в [docs/testing/ubuntu-docker.md](docs/testing/ubuntu-docker.md).
