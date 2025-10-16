# Аналитика и BI

## Стек

- **Superset** — рекомендованный BI слой. Подключайте через SQLAlchemy URI к PostgreSQL.
- **Metabase** — поддерживаемая альтернатива для быстрых дашбордов.

## ETL-пайплайн

- Реализован в `backend/services/analytics_pipeline.py`.
- Планировщик: Celery (`analytics.run_pipeline`) + Redis.
- Источники: `tasks`, `support_tickets`, `integration_connections`, `docs`.
- Хранилище витрин: таблица `analytics_snapshots` (metric, bucket, payload).

## Регулярные задачи

| Задача | Частота | Команда |
| ------ | ------- | ------- |
| `analytics.run_pipeline` | каждый час | Celery beat / Kubernetes CronJob |
| `integration.sync_*` | по расписанию | Celery |

## BI-дэшборды

1. **Delivery Velocity** — использует snapshots `metric=velocity`.
2. **Support SLA** — snapshots `metric=support`.
3. **Platform Overview** — snapshot `metric=summary`.

Для Superset создайте dataset `analytics_snapshots`, настройте virtual dataset c фильтром `metric = '<название>'`.
