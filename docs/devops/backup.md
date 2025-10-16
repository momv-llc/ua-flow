# Бэкап и восстановление БД UA FLOW

## PostgreSQL (production)

1. Создайте S3-совместимое хранилище и укажите креденшелы в секретах:
   - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`
   - `BACKUP_BUCKET`, `BACKUP_PREFIX`
2. Настройте cronjob (например, Kubernetes CronJob) с образом `postgres:16`:

```bash
pg_dump --format=custom --file=/tmp/uaflow.dump \
  --host "$PGHOST" --port "$PGPORT" \
  --username "$PGUSER" "$PGDATABASE"
aws s3 cp /tmp/uaflow.dump "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/uaflow-$(date +%F).dump"
```

3. Для восстановления выполните:

```bash
aws s3 cp "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/uaflow-<date>.dump" /tmp/restore.dump
pg_restore --clean --create --dbname=postgres \
  --host "$PGHOST" --port "$PGPORT" \
  --username "$PGUSER" /tmp/restore.dump
```

## SQLite (локальная разработка)

Используйте встроенный скрипт `scripts/backup_db.sh`:

```bash
./scripts/backup_db.sh
```

Скрипт создаёт бэкап в `backups/uaflow-<timestamp>.db` и поддерживает ротацию.
