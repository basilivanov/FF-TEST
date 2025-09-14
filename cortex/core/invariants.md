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

### Logging (V3) — Инварианты

- Формат: только JSON‑строки (одна строка на событие). Обязательные поля: `ts` (UTC RFC3339), `level`, `env`, `component`, `agent_role`, `correlation_id`, `event`. Детали — в `kv{}`.
- Корреляция: во всех HTTP запросах обязателен `X-Correlation-Id`; прокидывается через все подсистемы.
- Безопасность: секреты/токены/authorization редактируются процессором (`***`), payload’ы не логируются целиком.
- Производительность: DEBUG включается точечно (по подсистемам) и/или через TTL‑профили; в PROD по умолчанию `INFO` (DB/LLM — не ниже `WARN`).
- Сэмплинг и троттлинг: `LOG_DEBUG_SAMPLE_N` (1 из N DEBUG‑событий), `LOG_WARN_THROTTLE_WINDOW_SEC` (подавление повторов WARN в окне). Значения читаются из ENV и применяются централизованно.
- Единый конфиг: централизованная настройка в `app/logging/config.py`; уровни можно менять на лету через админ‑эндпоинты.
- События: именование `snake_case`, глагол+сущность (`api_call_start`, `github_api_call_response`), список стандартизован в reference.
- **Секреты:** Обязательная редакция в `***REDACTED***`

## Task Handoff Protocol
- **Формат:** Строго одно сообщение = один YAML блок
- **Обязательные поля:** `task`, `corr_id`, `context`, `prechecks`, `plan`, `dod`, `artifacts_dir`
- **Путь:** Все пути абсолютные, все URL полностью квалифицированы
- **DoD:** Критерии приёмки должны быть проверяемыми
