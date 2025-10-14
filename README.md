# UA FLOW — MVP

Рабочий минимальный продукт по ТЗ: FastAPI backend + React (Vite) frontend + PostgreSQL. 
Запуск через Docker Compose.

## Быстрый старт

```bash
docker compose up --build
```

- Backend API (Swagger): http://localhost:8000/docs
- Frontend UI:        http://localhost:5173

## Дефолтные креды

После регистрации через UI/или POST /api/v1/auth/register — войдите в систему.
Роли: `admin`, `user`. По умолчанию создаются пользователи с ролью `user`.

## Переменные окружения (пример)

Смотри `.env.example`. Для локального docker-compose значения уже прописаны.
