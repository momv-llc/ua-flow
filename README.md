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
- `/api/v1/billing` — тарифы, способы оплаты, подписки и журналы транзакций.

## Дефолтные креды

После регистрации через UI/или POST /api/v1/auth/register — войдите в систему.
Роли: `admin`, `user`. По умолчанию создаются пользователи с ролью `user`.

## Переменные окружения (пример)

Смотри `.env.example`. Для локального docker-compose значения уже прописаны.

> ℹ️ Если переменная `DATABASE_URL` не задана, backend автоматически
> использует локальную базу SQLite (`uaflow.db`). Это позволяет запустить
> API без внешнего PostgreSQL. Для продакшна обязательно укажите
> `DATABASE_URL` со строкой подключения к PostgreSQL.

## Очереди интеграций и аналитики

- Redis поднимается автоматически (`redis` сервис в `docker-compose.yml`).
- Celery-воркер запускается отдельным сервисом `worker` (команда `celery -A backend.celery_app.celery_app worker`).
- Настройки брокера и результата настраиваются переменными `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`. Для локальной разработки включён eager-режим (задачи выполняются синхронно при отсутствии Redis).
- Подробные спецификации обмена и песочницы описаны в [docs/integrations/](docs/integrations/README.md).
- ETL пайплайн описан в [docs/analytics/README.md](docs/analytics/README.md) и доступен через Celery-задачу `analytics.run_pipeline`.

## Локализация UI

Фронтенд использует i18next и поддерживает три языка: українська, English, русский. Переключатель языка доступен в шапке интерфейса и сохраняется в `localStorage`.

## CI/CD и релизный пайплайн

- GitHub Actions workflow: `.github/workflows/ci.yml` (см. [описание](docs/devops/ci_cd.md)).
- Генерация OpenAPI и Postman коллекции: `python scripts/export_openapi.py` (артефакты в [docs/api](docs/api)).
- Backend Docker образ собирается мультистадийным Dockerfile (`backend/Dockerfile`).
- Helm chart для Kubernetes: `deploy/helm/ua-flow-backend`.

## Зависимости для чистого сервера

1. **Системные пакеты**: `sudo apt-get install -y curl git build-essential python3 python3-venv python3-pip`.
2. **Docker Engine + Compose**: [инструкция](https://docs.docker.com/engine/install/ubuntu/); убедитесь, что `docker compose version ≥ 2.20`.
3. **Node.js 20 LTS**: через `nvm`, `fnm` или официальный репозиторий Nodesource.
4. **PostgreSQL 15+ и Redis 7** (продакшн). Для локального запуска хватает SQLite и eager-режима Celery.
5. **GitHub Actions runner / Make / rsync** — опционально, для CI и выкладки чартов.

После установки зависимостей можно запускать проект через `docker compose up --build` или по отдельности (`pip install -r backend/requirements.txt`, `npm --prefix frontend install`, `npm --prefix frontend run build`, `uvicorn backend.main:app`).

## Состояние проекта

### Реализовано
- Модули Core, Tasks, Docs, Support, Integrations, Admin, Analytics и Billing — API, UI-страницы, i18n и темизация.
- Очереди Celery/Redis, smoke-тесты (`scripts/smoke_api.py`), OpenAPI/Postman экспорт, Helm-chart, GitHub Actions CI.
- Marketplace и Integration Hub с песочницами, а также расширенный дизайн-сет и шрифт Inter.

### Осталось
- Подключить боевые аккаунты LiqPay/Fondy/WayForPay, 1С/Медок/СПІ/Дія и завершить интеграционное тестирование.
- Настроить промышленную БД PostgreSQL + объектное хранилище для документов/подписей.
- Добавить роль супер-администратора и разграничение прав для биллинга/финансов.

### Возможные расширения
- SDK для маркетплейса (хуки, UI-компоненты, REST-расширения).
- Автоматизация сверки оплат (банковские выписки, вебхуки провайдеров, OCR счетов).
- PWA/мобильные клиенты, push-уведомления, интеграция с корпоративными SSO.

## Резервное копирование

- PostgreSQL сценарии описаны в [docs/devops/backup.md](docs/devops/backup.md).
- Для локальной SQLite используйте `./scripts/backup_db.sh` — бэкап сохраняется в `backups/`.

## Проверка сборки в Ubuntu Docker

Для быстрой проверки совместимости зависимостей с чистым образом Ubuntu 24.04 выполните:

```bash
./scripts/test_ubuntu_docker.sh
```

Скрипт поднимет одноразовый контейнер `ubuntu:24.04`, установит Python и Node.js, соберёт фронтенд и выполнит компиляцию бэкенда. Подробнее — в [docs/testing/ubuntu-docker.md](docs/testing/ubuntu-docker.md).
