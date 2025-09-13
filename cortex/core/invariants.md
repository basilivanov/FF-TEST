# Критические инварианты FeatureFactory

## База данных
- **Схема:** Все изменения схемы только через Alembic (`alembic revision --autogenerate -m "description"` → `alembic upgrade head`)
- **Режим:** WAL режим обязателен в PROD (`SQLITE_JOURNAL_MODE=WAL`)
- **Таймауты:** `busy_timeout=5000ms` для предотвращения блокировок
- **ЗАПРЕЩЕНО:** Прямые SQL команды для изменения схемы (`ALTER TABLE`, `CREATE INDEX` и т.д.)

## Git операции
- **Базовая ветка:** `main` (никогда не коммитим в main напрямую)
- **SSH ключ:** `~/.ssh/id_ed25519_ff` для GitHub интеграции
- **Паттерн веток:** `feature/<id>_<slug>` для всех фич
- **PR workflow:** Обязательные проверки перед merge

## Секреты и конфигурация
- **Источник секретов:** Только `secret_store.get_secret(key)` из `cortex/security/credentials.md`
- **ЗАПРЕЩЕНО:** Хардкод секретов в коде или "придумывание" паролей
- **Логирование:** Все секреты редактируются в логах как `***REDACTED***`

## Запуск приложения
- **Корневая директория:** `uvicorn` запускается только из `/opt/feature-factory`
- **ЗАПРЕЩЕНО:** `uvicorn` из любой другой директории
- **Команда:** `cd /opt/feature-factory && uvicorn app.main:app`

## Логирование
- **Формат:** Только single-line JSON с обязательными полями
- **Поля:** `ts`, `level`, `env`, `component`, `agent_role`, `correlation_id`, `event`
- **Библиотеки:** `structlog` для JSON, `loguru` для ротации
- **Секреты:** Обязательная редакция в `***REDACTED***`

## Task Handoff Protocol
- **Формат:** Строго одно сообщение = один YAML блок
- **Обязательные поля:** `task`, `corr_id`, `context`, `prechecks`, `plan`, `dod`, `artifacts_dir`
- **Путь:** Все пути абсолютные, все URL полностью квалифицированы
- **DoD:** Критерии приёмки должны быть проверяемыми