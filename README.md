# UA FLOW — MVP

Рабочий минимальный продукт по ТЗ: FastAPI backend + React (Vite) frontend + PostgreSQL.
Бэкенд реализует модули Core/Docs/Support/Integration/Admin/Analytics c JWT и 2FA.
Запуск через Docker Compose.

## Быстрый старт

```bash
docker compose up --build
```

- Backend API (Swagger): http://localhost:8000/docs
- Frontend UI:        http://localhost:5173

### Основные REST-модули

- `/api/v1/auth` — регистрация, вход, refresh-токены, 2FA (TOTP).
- `/api/v1/projects` — команды, проекты, спринты, эпики.
- `/api/v1/tasks` — Kanban/Scrum задачи, комментарии, отчёты.
- `/api/v1/docs` — вики-документы с версионностью и подписями (КЕП).
- `/api/v1/support` — service desk, SLA, комментарии, назначения.
- `/api/v1/integrations` — Integration Hub (1C, Medoc, SPI, Diia, Prozorro, Webhooks).
- `/api/v1/admin` — управление пользователями, настройками, аудитом.
- `/api/v1/analytics` — метрики, тепловые карты тикетов, загрузка.

## Дефолтные креды

После регистрации через UI/или POST /api/v1/auth/register — войдите в систему.
Роли: `admin`, `user`. По умолчанию создаются пользователи с ролью `user`.

## Переменные окружения (пример)

Смотри `.env.example`. Для локального docker-compose значения уже прописаны.
