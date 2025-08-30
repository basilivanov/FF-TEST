# Schema-000: Базовые таблицы MVP

## Конфигурация БД

### Стандартизированные пути к базам данных:
- **TEST окружение**: `sqlite:////opt/feature-factory/data/test.db`
- **PROD окружение**: `sqlite:////opt/feature-factory/data/prod.db` 
- **INDEX окружение**: `sqlite:////opt/feature-factory/data/index.db`

Все компоненты системы используют переменную окружения `DATABASE_URL` с корректными дефолтными значениями для соответствующего окружения.

## Структура таблиц

## postings_raw
- id INTEGER PK AUTOINCREMENT
- source TEXT NOT NULL  (e.g., "ozon")
- posting_id TEXT NOT NULL
- payload_json TEXT NOT NULL
- fetched_at DATETIME NOT NULL
- period_from DATE NULL
- period_to DATE NULL
- UNIQUE (source, posting_id)

## postings_flat
- source TEXT NOT NULL
- posting_id TEXT NOT NULL
- sku TEXT NOT NULL
- qty INTEGER NOT NULL
- price NUMERIC NOT NULL
- discount_mp NUMERIC NULL
- final_price NUMERIC NOT NULL
- posting_date DATE NOT NULL
- UNIQUE (source, posting_id, sku)

## etl_watermarks
- source TEXT PRIMARY KEY
- last_successful_iso DATETIME NOT NULL

## jobs
- id INTEGER PK AUTOINCREMENT
- name TEXT NOT NULL
- params_json TEXT
- status TEXT CHECK(status IN ('NEW','RUNNING','DONE','RETRYABLE_ERROR','FAILED')) NOT NULL
- started_at DATETIME
- finished_at DATETIME
- result_json TEXT
- retries INTEGER DEFAULT 0

## settings
- key TEXT PRIMARY KEY
- value TEXT NOT NULL

## agent_events
- id INTEGER PK AUTOINCREMENT
- ts DATETIME NOT NULL
- agent_role TEXT NOT NULL  -- Maintainer|Architect|Dev|QA|Scribe|System
- task_id TEXT
- event TEXT NOT NULL       -- см. Logging-001
- details_json TEXT NOT NULL

## doc_registry
- doc_name TEXT PRIMARY KEY  -- напр., "docs/Logging-001.md"
- version TEXT NOT NULL      -- семвер/метка
- content_hash TEXT NOT NULL
- updated_at DATETIME NOT NULL

## change_log
- id INTEGER PK AUTOINCREMENT
- ts DATETIME NOT NULL
- agent_role TEXT NOT NULL
- artifact_manifest_json TEXT NOT NULL
- commit_id TEXT NULL
- related_docs TEXT NULL

## features (новая таблица)
- id INTEGER PK AUTOINCREMENT
- title TEXT NOT NULL
- intent_json TEXT
- status TEXT CHECK(status IN ('NEW','PLANNED','RUNNING','DONE','FAILED')) NOT NULL
- priority INTEGER
- created_at DATETIME NOT NULL
- created_by TEXT
- env TEXT

## tasks (новая таблица)
- id INTEGER PK AUTOINCREMENT
- feature_id INTEGER NOT NULL FK → features.id
- role TEXT NOT NULL
- dsl_json TEXT
- status TEXT CHECK(status IN ('NEW','RUNNING','DONE','RETRYABLE_ERROR','FAILED')) NOT NULL
- attempts INTEGER
- budget_tokens INTEGER
- scheduled_at DATETIME
- started_at DATETIME
- finished_at DATETIME

## graph_runs (новая таблица)
- run_id TEXT PRIMARY KEY
- feature_id INTEGER NOT NULL FK → features.id
- graph_name TEXT NOT NULL (например, 'G1')
- thread_id TEXT
- state_json TEXT
- status TEXT
- last_checkpoint_at DATETIME
- env TEXT

### Ограничения уникальности

Для обеспечения единственности активного run для каждой фичи в каждом окружении, необходимо добавить одно из следующих ограничений:

1.  **Уникальный индекс на (feature_id, env) с проверкой статуса**: Приложение должно проверять, что для данной комбинации `(feature_id, env)` может существовать только один run со статусом `NEW`, `RUNNING` или `PENDING`.

2.  **Добавить поле `active` и уникальный индекс**: Добавить булево поле `active` и создать уникальный индекс на `(feature_id, env, active=true)`.

### Идемпотентность
- Import: upsert по (source, posting_id), watermark двигается после успеха серии.
- Normalize: replace батчами; ключ (source, posting_id, sku).
- Export Sheets: перезапись диапазона.
- Миграции: идемпотентны (могут применяться повторно без ошибок).

### Миграции
- Используется Alembic для управления миграциями базы данных.
- Первая миграция (0001_init) создает все базовые таблицы.
- Миграция backlog (7f0adda46c0c) добавляет таблицы features, tasks, graph_runs.
- Для применения миграций используется команда `alembic upgrade head`.
