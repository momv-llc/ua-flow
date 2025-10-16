# UA Marketplace: Hooks & Расширения

## Backend Hooks

| Точка расширения | Описание | Пример |
| ---------------- | -------- | ------ |
| `integration_runner.register_connector` | Регистрация кастомного коннектора | Передать класс клиента и описания схем |
| `tasks.register_listener` (план) | Отправка вебхуков при изменении задач | Создание уведомлений в внешних системах |
| Celery task `analytics.run_pipeline` | Подмешивание собственных витрин | Вызывать дополнительный ETL перед коммитом snapshot |

## Webhooks

- `POST /api/v1/integrations/webhooks/preview` — тестирование payload.
- Для боевых интеграций используйте `integration_connections.settings.webhook_url`.
- Подпись запросов: добавьте заголовок `X-UA-Signature` с HMAC-SHA256.

## UI-компоненты

Frontend поддерживает lazy-загрузку модулей через `src/pages/marketplace/Marketplace.jsx`. Для кастомных виджетов:

1. Экспортируйте компонент из пакета `@uaflow/extensions` (создаётся разработчиком).
2. Добавьте запись в `MarketplaceApp` с `settings.render = "package:Component"`.
3. Клиент подгрузит модуль через dynamic import и встроит в дэшборд.

## Публикация пакета

1. Подготовьте README с описанием коннектора/виджета.
2. Загрузите архив через REST `POST /api/v1/integrations/marketplace` (планируется) или через админку.
3. После модерации приложение станет доступно в каталоге.
