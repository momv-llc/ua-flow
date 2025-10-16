# CI/CD и секреты

## GitHub Actions

Pipeline `.github/workflows/ci.yml` выполняет:

1. Установку Python зависимостей и базовую проверку `compileall`.
2. Смоук-тест API (`scripts/smoke_api.py`).
3. Генерацию OpenAPI + Postman (`scripts/export_openapi.py`).
4. Сборку фронтенда (`npm --prefix frontend run build`).
5. Сборку Docker-образа backend.

Добавьте шаги деплоя (ArgoCD/Flux) по мере готовности инфраструктуры.

## Секреты и конфигурация

- Используйте переменные окружения в GitHub Secrets: `DATABASE_URL`, `JWT_SECRET`, `BROKER_URL`, `RESULT_BACKEND`.
- Для Kubernetes применяйте `*_FILE` переменные (`DATABASE_URL_FILE`, `JWT_SECRET_FILE`). Backend читает файлы через `backend.secrets.get_secret`.
- Рекомендуемый Secret Manager: HashiCorp Vault или AWS Secrets Manager с автоматическим ротационным полиси.

## Release Flow

1. Pull Request → автоматический CI.
2. Merge → Git tag `vX.Y.Z`.
3. GitHub Actions вызывает Helm chart деплой (`deploy/helm/ua-flow-backend`).
4. После деплоя выполните `celery -A backend.celery_app.celery_app call analytics.run_pipeline` для прогрева витрин.
