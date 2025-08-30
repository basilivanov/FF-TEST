# FF-Handbook-BUNDLE.md

*Собранный handbook проекта Feature Factory*

---

## Файл: app/agents/prompts/_capsule.md

# КАПСУЛА КОНТЕКСТА v1.2 — Фабрика бизнес‑фич (MVP)

## Инварианты
- Один VPS; окружения: **test (8081, DRY_RUN=true, без APScheduler)** / **prod (8080, DRY_RUN=false)**.
- Стек: FastAPI; SQLite+SQLAlchemy+Alembic; APScheduler; httpx(+tenacity); sqladmin; structlog; LangGraph; LiteLLM.
- **Python 3.12**, стиль PEP8, типы обязательны; докстринги Google-style.
- Идемпотентность: upsert, уникальные ключи, watermark (повторный запуск — без дублей).
- Логи: **Logging-001** — JSON one-line, поля и события стандартизованы.
- Тесты: критическая логика ≥70% веток; E2E на пайплайн.
- TZ по умолчанию: Europe/Moscow; Sheets — формулы с `;`.

## Роли
- **Maintainer** — интерфейс для человека (NL). Понимает задачу «человеческим языком», выясняет недостающее, предлагает дефолты, формирует **намерение** и ставит задачи **Architect** либо напрямую **Dev/QA/Scribe** в DSL. Держит контекст продукта/ключей/расписаний, следит за DocSync.
- **Architect** — план (DAG), контракты, схемы, DoD, бюджеты; **не пишет код**.
- **Dev** — код/миграции строго по контракту; возвращает **artifact_manifest** и файлы.
- **Validator (QA)** — unit/integration/E2E тесты + отчёт; код не чинит.
- **Scribe** — документация (Architecture/Ops/Commands/ADR/CHANGELOG) по **DocSync**.
- **Orchestrator** — исполняет граф, ретраи/квоты, валидирует форматы, триггерит DocSync.

## Форматы
- **DSL задачи (минимум)**:
```json
{
  "id":"uuid","name":"ingest_ozon_range","kind":"job|code|doc|test","role":"Architect|Dev|QA|Scribe",
  "preconditions":["..."],"postconditions":["..."],
  "idempotency_key":"...","retry":{"max":2,"backoff":"exp:5,30,120"},
  "deadline":"PT10M","models":["flash","qwen-fallback"],
  "outputs":["files|logs|tables"],"dod":["..."],"severity":"low|med|high"
}
```
- Ответ Dev/QA/Scribe: **сначала** YAML `artifact_manifest`, затем файлы в fenced-блоках (```python / ```sql / ```yaml). Патчи — unified diff или цельные файлы.
- Код — **только** в fenced-блоках; без «воды».

## Политики LLM
- Бюджеты: Architect ≤1800; Dev ≤1400; QA ≤800; Scribe ≤800; `temperature=0`.
- Fallback: Flash → Qwen → wait. 429/5xx → ретрай с backoff.
- Валидация ответа: нарушение формата → 1 ретрай с указанием недочёта.

## Идемпотентные ключи (MVP)
- `postings_raw`: `(source, posting_id)`
- `postings_flat`: `(source, posting_id, sku)`
- Watermark двигаем **после полного успеха** батча.

## Логи (JSON, Logging-001)
`{ "ts", "level", "env", "component", "agent_role", "run_id", "task_id", "correlation_id", "event", "kv": {...} }`

## Неисправности — реакции
- `Network/RateLimit` → ретрай + backoff.
- `AuthError` → FAIL + уведомление; не ретраить.
- `SchemaError` → FAIL + баг-задача на маппинг; запрещено «чинить молча».
- Нехватка квот LLM → задачи роли в «ожидание»; runtime-джобы продолжаются.

## LLM‑навигация по коду (быстро и дёшево)
- Индексер (repo‑map): **ctags (symbols) + pyan3 (call‑graph) + module‑cards**; API `/api/v1/index/*`.
- В начале каждого модуля — блок **LLM-NAV:** Purpose, Public API, Inputs/Outputs, Side effects, Depends on, Used by.
- В промпты подаём **символы/фрагменты** по ответу индексера, не весь файл.

## Natural‑Language интерфейс
- Пользователь пишет обычно. **Maintainer** преобразует запрос в **intent+slots** (см. `docs/Commands-NL.md`, `app/ui/nl_intents.yaml`) и/или формирует задачи в DSL для ролей.
- Команды‑пример: «Импортируй Озон за вчера», «Сделай отчёт в Гугл Шитс вкладка Продажи‑день на A1», «Поставь расписание импорта на 09:15 по будням».


---

## Файл: app/agents/prompts/architect.md

# SYSTEM — Architect (LLM)

Прочти `_capsule.md` полностью и соблюдай дословно.

**Роль:** системный архитектор. Ты НЕ генерируешь код. Твоя задача — превратить входной бизнес‑запрос в детерминированный DAG из задач DSL, описать контракты (схемы/миграции/интерфейсы), DoD и бюджеты.

**Требования к ответу:**
- Сначала краткий план‑буллеты.
- Затем массив JSON‑объектов задач в точном DSL (каждый — короткий и независимый).
- У каждой задачи: `preconditions`, `postconditions`, `idempotency_key`, `retry`, `models`, `dod`.
- Миграции/схемы всегда раньше кода; QA и Scribe — после.
- Пути файлов указывать явно (snake_case). Дроби задачи под бюджеты Flash.

**Формат вывода:**
1) `## План` — буллеты.
2) `## Задачи (DSL)` — JSON‑массив в одном fenced‑блоке.


---

## Файл: app/agents/prompts/developer.md

# SYSTEM — Developer (LLM) [логирование обязательно]

Прочти `_capsule.md` полностью. Работай строго по контракту Architect.

**Роль:** бэкенд‑разработчик Python. Возвращаешь только артефакты.

**Правила разработки:**
- Python 3.12, PEP8, типы обязательны (`from __future__ import annotations`).
- HTTP: `httpx` (async), таймауты connect=3s, read=10s, ретраи `tenacity` с джиттером.
- БД: `SQLAlchemy` + Alembic; upsert (`ON CONFLICT DO UPDATE`/эквивалент); транзакции батчами.
- Конфиги: `pydantic-settings`; не использовать `os.getenv` напрямую.
- Логи: `structlog` JSON; без секретов/PII. Используй **logging_helpers**:
  - оборачивай джобы в `@log_job("job_name")`
  - HTTP вызовы через `@log_http`
  - операции БД через `@log_db`
  - для LLM — `llm_log_context()` (model, prompt_hash, tokens)
- Джобы — идемпотентны: уникальные ключи и watermark.
- Выдавай **сначала** YAML `artifact_manifest`, затем файлы (fenced).

**Формат ответа:**
1) ```yaml  # artifact_manifest```
2) Файлы в ```python/```sql/```yaml блоках.


---

## Файл: app/agents/prompts/maintainer.md

# SYSTEM — Maintainer (LLM)

**Роль:** интерфейс между человеком и системой. Понимаешь натуральный русский язык, уточняешь недостающее, предлагаешь дефолты, переводишь запрос в **intent+slots** и/или в набор задач DSL для Architect/Dev/QA/Scribe. Следишь за DocSync (если артефакты поменялись — ставишь Scribe задачу на обновление).

**Требования:**
- Первым блоком верни краткую интерпретацию запроса человека.
- Затем **intent JSON** по `docs/Commands-NL.md` (строго по схеме).
- Если нужен план реализации — сформируй компактный DAG (DSL) для Architect.
- Если хватает данных для прямого вызова job — верни команду для Orchestrator (machine intent), но человек это не видит.
- Проверяй DRY_RUN и окружение (test/prod).

**Запрещено:** выполнять код/генерировать арты; ты координируешь и планируешь.


---

## Файл: app/agents/prompts/scribe.md

# SYSTEM — Scribe (LLM) [DocSync]

Прочти `_capsule.md`. Пиши кратко, по делу.

**Роль:** техписатель. Обновляешь `docs/Architecture.md`, `docs/Ops.md`, `docs/Commands*.md`, ADR при изменениях.

**DocSync — обязательно:**
- На вход всегда приходит `artifact_manifest`. Определи, какие документы обновить.
- Если изменены `logging.py`/`logging_helpers.py` → обнови `docs/Logging-001.md` (версию ↑, дату).
- Если изменены схемы/миграции → обнови `docs/Schema-000-*.md`.
- Всегда обновляй `CHANGELOG.md` (Added/Changed/Fixed) со списком файлов.
- В ответе верни событие `doc_updated` в summary.

**Формат ответа:**
1) ```yaml # artifact_manifest```
2) Файлы Markdown (fenced).


---

## Файл: app/agents/prompts/validator.md

# SYSTEM — Validator (QA, LLM)

Прочти `_capsule.md`. Проверяй соответствие договорённостям.

**Роль:** QA‑инженер. Генерируешь unit/integration/E2E тесты и отчёт. Код НЕ правишь.

**Правила:**
- Покрытие критических путей ≥70% веток.
- Моки внешних API (Ozon, Sheets); негативные/граничные случаи обязательны.
- E2E: импорт(вчера) → нормализация → экспорт.
- Отчёт Markdown: Steps / Expected / Actual / Gaps / Recommendations.

**Формат ответа:**
1) ```yaml # artifact_manifest``` — пути тестов
2) Файлы тестов (fenced)
3) ```markdown``` — отчёт


---

## Файл: docs/Architecture.md

# Architecture (MVP)
- Окружения: test (8081, DRY_RUN=true, без APScheduler), prod (8080, DRY_RUN=false).
- Роли: Maintainer (NL интерфейс), Architect, Dev, QA, Scribe, Orchestrator.
- Оркестрация: LangGraph; роутер LLM — LiteLLM.
- Данные: SQLite, Alembic; JSON хранится в TEXT; взрыв JSON в Python.
- Индексация кода: scripts/index.sh → ctags (symbols), pyan3 (call-graph), module-cards; API `/api/v1/index/*`.

## База данных и миграции
- Используется Alembic для управления миграциями базы данных.
- Миграции хранятся в `app/db/migrations/versions`.
- Для применения миграций используется команда `alembic upgrade head`.

## Индексер кода
- Реестр кода: `code_registry` (файлы и их хэши)
- Индекс символов: `symbol_index` (классы, функции и другие символы)
- Граф вызовов: `call_graph_edges` (связи между символами)
- Инструменты: ctags (символы), pyan3 (граф вызовов)
- API: `/api/v1/index/symbol`, `/api/v1/index/calls`

## Логи
- Стандарт и профили — `docs/Logging-001.md`.
- Корреляция: `correlation_id` на вход HTTP/джоб; `run_id` — на конвейер.
- Инструментирование через `logging_helpers` декораторы.

## DocSync
- Orchestrator слушает `artifact_manifest` → `change_log` → Scribe.
- `doc_registry` хранит версию/hash каждого документа.
- Команды админки: `/docs status`, `/docs rebuild`.


---

## Файл: docs/Schema-000-base-tables.md

# Schema-000: Базовые таблицы MVP

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

### Идемпотентность
- Import: upsert по (source, posting_id), watermark двигается после успеха серии.
- Normalize: replace батчами; ключ (source, posting_id, sku).
- Export Sheets: перезапись диапазона.

### Миграции
- Используется Alembic для управления миграциями базы данных.
- Первая миграция (0001_init) создает все таблицы, описанные выше.
- Для применения миграций используется команда `alembic upgrade head`.


---

## Файл: docs/ChangePolicy-000.md

# Change Policy (MVP)

## События системы

### Общие
- `job_scheduled` `job_started` `job_finished` `retry_scheduled` `rate_limited` `error`

### HTTP
- `api_call_start` `api_call_end`

### БД
- `db_upsert` `db_replace_batch` `db_migration_applied`

### LLM
- `llm_call_start` `llm_call_end` `llm_budget_exceeded` `llm_output_invalid`

### ETL
- `extract_page` `transform_batch` `load_batch` `watermark_advanced`

### Sheets
- `sheets_write_start` `sheets_write_end`

### Docs/Change
- `artifact_applied` `doc_updated` `changelog_written` `index_updated`

## Политики

### 1. `index_updated`
- **Инициатор:** Dev (скрипт индексации)
- **Условия:** При успешном обновлении реестра кода и индексов
- **Действия:** 
  - Логирование события в систему логов
  - Обновление времени последней индексации
- **Мониторинг:** QA отслеживает регулярность событий

---

## Файл: docs/Logging-001.md

# Logging-001: Единый стандарт логов (v1.1)
- **Цель:** одинаковые, парсируемые, информативные логи во всех модулях; дешёвые по объёму; без секретов.
- **Библиотеки:** structlog (JSON) + loguru (ротация). Все записи — только **JSON одной строки**.

## 1) Обязательные поля
- `ts`, `level`, `env`, `component`, `agent_role`, `run_id`, `task_id`, `correlation_id`, `event`, `kv{}`

## 2) Каталог событий
- Общие: `job_scheduled` `job_started` `job_finished` `retry_scheduled` `rate_limited` `error`
- HTTP: `api_call_start` `api_call_end`
- БД: `db_upsert` `db_replace_batch` `db_migration_applied`
- LLM: `llm_call_start` `llm_call_end` `llm_budget_exceeded` `llm_output_invalid`
- ETL: `extract_page` `transform_batch` `load_batch` `watermark_advanced`
- Sheets: `sheets_write_start` `sheets_write_end`
- Docs/Change: `artifact_applied` `doc_updated` `changelog_written`

## 3) Профили kv
- HTTP: `{method,url_host,url_path,status,duration_ms,attempt,retries,backoff_ms,req_bytes,resp_bytes}`
- БД: `{table,op,rows,conflicts,duration_ms}`
- LLM: `{provider,model,prompt_hash,input_tokens,output_tokens,latency_ms,cache_hit,budget_remaining}`
- ETL: `{source,page,items,total,window_from,window_to}`
- Sheets: `{spreadsheet_id,sheet,range,rows,cols,duration_ms}`

## 4) Уровни/сэмплинг
- INFO по умолчанию; DEBUG ≤5% (kv.sampling). ERROR: `err_type`,`err_msg` (без секретов), `stack:true`.

## 5) Маскирование
- Токены/секреты/PII → `***REDACTED***`. Payload не логируется.

## 6) Корреляция
- `correlation_id` на входе HTTP/джобы; `run_id` — на весь конвейер.

## 7) Helpers
- `@log_job`, `@log_http`, `@log_db`, `llm_log_context()` — обязательны для Dev.


---

## Файл: docs/Policy-LLM-000.md

# Policy-LLM-000: Модели, бюджеты, форматы
- Роли/бюджеты: Architect ≤1800; Dev ≤1400; QA ≤800; Scribe ≤800; Maintainer ≤900; temperature=0.
- Маршрутизация: Flash по умолчанию; fallback Qwen; при наличии квот — Architect/Maintainer могут быть Claude/GPT.
- Таймаут LLM: 30s; 1 ретрай при нарушении формата.
- Формат ответов: см. капсулу. Код — только в fenced‑блоках.
- Учёт токенов: оркестратор ведёт счёт по ролям/суткам; при исчерпании — постановка в очередь «на завтра».


---

## Файл: docs/Security-000.md

# Security-000: Секреты и доступ
- Секреты: только через `.env`/переменные окружения; `.env` не коммитим.
- Доступ к БД: один пользователь, минимум прав; бэкапы ежедневно.
- Сеть: whitelist доменов (Ozon/WB/Google).
- UI: BasicAuth (MVP), HTTPS по возможности, httpOnly cookies.
- Sandbox исполнения сгенерённого кода: отдельный пользователь без sudo.


---

## Файл: docs/Commands-NL.md

# Commands-NL: Натуральный язык → интенты → действия

## Схема `intent`
```json
{
  "intent": "plan_feature|run_import_ozon|run_normalize|run_export_sheets|set_schedule|status_jobs|logs_tail|docs_status|docs_rebuild|dry_run_toggle",
  "env": "test|prod",
  "slots": { "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "sheet": "Имя", "range": "A1", "time": "HH:MM", "days": "mon-fri", "component": "job|db|llm|*", "level": "INFO|ERROR", "last": 200, "on": true }
}
```

## Примеры → intent
- «Импортируй Озон за вчера в тесте» → `{intent:"run_import_ozon", env:"test", slots:{from:"yesterday", to:"yesterday"}}`
- «Сделай отчёт в гугл шитс Продажи‑день на A1» → `{intent:"run_export_sheets", slots:{sheet:"Продажи-день", range:"A1"}}`
- «Поставь импорт по будням на 09:15» → `{intent:"set_schedule", slots:{time:"09:15", days:"mon-fri"}}`
- «Покажи последние 100 ошибок БД» → `{intent:"logs_tail", slots:{component:"db", level:"ERROR", last:100}}`

## Потоки
1) User → Maintainer (NL)
2) Maintainer → (а) Architect с задачами DSL **или** (б) Orchestrator с machine‑intent, если всё ясно.
3) Orchestrator исполняет/планирует, Scribe обновляет документы (DocSync).


---

## Файл: docs/Commands-000.md

# Commands-000: Операции
- Интерфейс для человека — **натуральный язык** (см. `Commands-NL.md`).
- Внутри системы — **machine‑intents** и/или DSL‑задачи.
- Для обратной совместимости допустимы короткие слеш‑команды в админке.

### Примеры человек → система
- «Спланируй фичу: Озон RAW→Flat→Sheets»
- «Импортируй Озон за 2025‑08‑20…2025‑08‑21»
- «Экспортируй в Шитс вкладка Продажи‑день на A1»
- «Включи dry‑run в тесте»
- «Покажи статус последних 20 задач»
- «Хвост логов LLM ошибок 200 строк»


---

## Файл: docs/ADR-001-stack.md

# ADR-001: Стек MVP
- **Статус:** accepted
- **Дата:** 2025-08-21
- **Контекст:** один VPS (2 GB RAM); малые объёмы данных; агенты на Flash.
- **Решение:** FastAPI; SQLite+SQLAlchemy+Alembic; APScheduler; httpx; sqladmin; structlog; LangGraph; LiteLLM.
- **Почему так:** минимальные зависимости; низкая память; простая поддержка; чёткие контракты для агентов.
- **Альтернативы:** Django+Postgres (тяжелее), Airflow/Prefect (избыточно), ручная оркестрация (менее формально).
- **Последствия:** JSON‑взрыв делаем в Python; конкуренцию ограничиваем; миграции простые.
- **Риски:** дрейф API маркетплейсов → свой httpx‑клиент и QA‑моки.


---

## Файл: docs/DoD-000.md

# DoD-000: Готовность
- Дважды прогнанный конвейер не создаёт дублей; watermark корректен.
- Юнит‑покрытие критических модулей ≥70%; интеграционные тесты с моками; E2E «вчера».
- Команды доступны в UI (NL → intents); есть dry‑run.
- Документация обновлена (версии/даты).


---

## Файл: docs/Logging-000.md

# Logging-000 (deprecated)
См. актуальный стандарт: **Logging-001.md (v1.1)**.


---

---

## Файл: docs/QA-Policy-001.md

# QA Policy 001 — Требования к тестированию

## Запрещённые практики — список с regex-примерами, напр.:

assertIn\(response.status_code, \[.*200.*\] → запрещено

requests\.post\( в юнитах без TestClient — запрещено

:memory: / произвольные имена БД в тестах — запрещено

## Обязательные проверки — статусы, JSON-схемы, запись в БД, логи (event-коды).

## Шаблон тест-кейса — Given/When/Then; фикстура БД; фикстура capsule_system_prompt.

## Политика Gate — нарушение → qa_policy_violation + причины.
---

## Файл: docs/API-Orchestrator-001.md

# API-Orchestrator-001: Спецификация API оркестратора

## Общие принципы

- Все успешные ответы возвращают HTTP статус 200.
- Все ошибки возвращают статус 4xx с телом ответа, содержащим поле `error_code`.
- Все эндпоинты находятся под префиксом `/api/v1/orchestrator`.

## Эндпоинты

### POST /api/v1/orchestrator/features

Создает новую фичу в системе.

**Request Body (JSON):**
```json
{
  "title": "string",
  "intent": "object or null"
}
```

**Идемпотентность:**
Комбинация `(title, env)` уникальна. При повторном запросе с теми же параметрами возвращается 200 с существующим id и status.

**Response (200):**
```json
{
  "id": "integer",
  "status": "NEW|PLANNED|RUNNING|DONE|FAILED"
}
```

### POST /api/v1/orchestrator/features/{id}/plan

Вызывает Architect (через Router) для создания задач.

**Response (200):**
```json
{
  "feature_id": "integer",
  "tasks": [
    {
      "id": "integer",
      "role": "string",
      "status": "NEW"
    }
  ],
  "package_contract": "object"
}
```

### POST /api/v1/orchestrator/features/{id}/run

Запускает или возобновляет выполнение графа G1 (Dev→Gate→QA→Scribe→Apply).

**Response (200):**
```json
{
  "run_id": "string",
  "state": "STARTED|RESUMED"
}
```

### GET /api/v1/orchestrator/graph/{run_id}/status

Получает статус выполнения графа.

**Response (200):**
```json
{
  "run_id": "string",
  "graph": "G1",
  "status": "RUNNING|DONE|FAILED",
  "last_checkpoint": "string"
}
```

## JSON Schema

Для каждого ответа определена JSON Schema:
- R0-FeatureCreated.json
- R1-Plan.json
- R2-Run.json
- R3-GraphStatus.json

Схемы находятся в `app/api/schemas/orchestrator/.

---

## Файл: app/api/schemas/orchestrator/R0-FeatureCreated.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer"
    },
    "status": {
      "type": "string",
      "enum": ["NEW", "PLANNED", "RUNNING", "DONE", "FAILED"]
    }
  },
  "required": ["id", "status"]
}
```

---

## Файл: app/api/schemas/orchestrator/R1-Plan.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "feature_id": {
      "type": "integer"
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer"
          },
          "role": {
            "type": "string"
          },
          "status": {
            "type": "string",
            "const": "NEW"
          }
        },
        "required": ["id", "role", "status"]
      }
    },
    "package_contract": {
      "type": "object"
    }
  },
  "required": ["feature_id", "tasks", "package_contract"]
}
```

---

## Файл: app/api/schemas/orchestrator/R2-Run.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "run_id": {
      "type": "string"
    },
    "state": {
      "type": "string",
      "enum": ["STARTED", "RESUMED"]
    }
  },
  "required": ["run_id", "state"]
}
```

---

## Файл: app/api/schemas/orchestrator/R3-GraphStatus.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "run_id": {
      "type": "string"
    },
    "graph": {
      "type": "string",
      "const": "G1"
    },
    "status": {
      "type": "string",
      "enum": ["RUNNING", "DONE", "FAILED"]
    },
    "last_checkpoint": {
      "type": "string"
    }
  },
  "required": ["run_id", "graph", "status", "last_checkpoint"]
}
```
---

## Файл: app/api/schemas/orchestrator_schemas.py

```python
#!/usr/bin/env python3
"""
Pydantic схемы для API оркестратора, соответствующие спецификации API-Orchestrator-001.md.
"""

from pydantic import BaseModel
from typing import Optional, List, Any, Dict, Union


# Схемы запросов
class FeatureCreateRequest(BaseModel):
    """Схема запроса на создание фичи."""
    title: str
    intent: Optional[Union[Dict[str, Any], None]] = None


# Схемы ответов
class FeatureCreatedResponse(BaseModel):
    """Схема ответа на создание фичи."""
    id: int
    status: str  # "NEW" | "PLANNED" | "RUNNING" | "DONE" | "FAILED"


class TaskPlanResponse(BaseModel):
    """Схема задачи в ответе на планирование."""
    id: int
    role: str
    status: str  # Всегда "NEW" согласно спецификации


class PlanResponse(BaseModel):
    """Схема ответа на планирование фичи."""
    feature_id: int
    tasks: List[TaskPlanResponse]
    package_contract: Dict[str, Any]


class RunResponse(BaseModel):
    """Схема ответа на запуск фичи."""
    run_id: str
    state: str  # "STARTED" | "RESUMED"


class GraphStatusResponse(BaseModel):
    """Схема ответа на запрос статуса графа."""
    run_id: str
    graph: str  # Всегда "G1" согласно спецификации
    status: str  # "RUNNING" | "DONE" | "FAILED"
    last_checkpoint: str


# Схемы ошибок
class ErrorResponse(BaseModel):
    """Схема ответа об ошибке."""
    error_code: str
    detail: str
```

---

## Файл: app/api/orchestrator_v2.py

```python
#!/usr/bin/env python3
"""
API оркестратора для интеграции UI/скриптов, реализация по спецификации API-Orchestrator-001.md.
"""

import time
import uuid
import os
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Импортируем схемы
from app.api.schemas.orchestrator_schemas import (
    FeatureCreateRequest,
    FeatureCreatedResponse,
    PlanResponse,
    TaskPlanResponse,
    RunResponse,
    GraphStatusResponse,
    ErrorResponse
)

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./feature.test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(prefix="/api/v1/orchestrator")


# Вспомогательные функции
def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_correlation_id(request: Request) -> str:
    """Получает correlation_id из заголовков запроса."""
    return request.headers.get("x-correlation-id", generate_correlation_id())


def log_api_call_start(request: Request, correlation_id: str, **kwargs):
    """Логирует начало API вызова."""
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            **kwargs
        }
    )


def log_api_call_end(request: Request, correlation_id: str, status_code: int, duration_ms: float, **kwargs):
    """Логирует завершение API вызова."""
    log.info(
        event="api_call_end",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            **kwargs
        }
    )


# Эндпоинты API
@router.post("/features", 
             response_model=FeatureCreatedResponse,
             responses={
                 400: {"model": ErrorResponse},
                 409: {"model": ErrorResponse}
             })
async def create_feature(
    request: Request,
    feature_request: FeatureCreateRequest
):
    """
    Создать фичу.
    
    Args:
        request: HTTP запрос
        feature_request: Данные для создания фичи
        
    Returns:
        FeatureCreatedResponse: Информация о созданной или найденной фиче
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    env = get_env()
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        title=feature_request.title
    )
    
    try:
        # Проверяем, есть ли уже фича с таким title и env (идемпотентность)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, status FROM features 
                    WHERE title = :title AND env = :env
                """),
                {
                    "title": feature_request.title,
                    "env": env
                }
            )
            existing_feature = result.fetchone()
            
            # Если фича уже существует, возвращаем её
            if existing_feature:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(
                    request,
                    correlation_id,
                    status_code=200,
                    duration_ms=duration_ms,
                    feature_id=existing_feature[0],
                    message="Feature already exists"
                )
                
                return FeatureCreatedResponse(
                    id=existing_feature[0],
                    status=existing_feature[1]
                )
            
            # Создаем новую фичу
            intent_json = json.dumps(feature_request.intent) if feature_request.intent else None
            
            result = conn.execute(
                text("""
                    INSERT INTO features (
                        title, intent_json, status, priority, created_at, created_by, env
                    ) VALUES (
                        :title, :intent_json, 'NEW', 0, datetime('now'), 'API', :env
                    )
                """),
                {
                    "title": feature_request.title,
                    "intent_json": intent_json,
                    "env": env
                }
            )
            
            feature_id = result.lastrowid
            conn.commit()
            
            # Логируем успешное завершение вызова
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                feature_id=feature_id
            )
            
            return FeatureCreatedResponse(
                id=feature_id,
                status="NEW"
            )
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create feature: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.post("/features/{feature_id}/plan",
             response_model=PlanResponse,
             responses={
                 400: {"model": ErrorResponse},
                 404: {"model": ErrorResponse}
             })
async def plan_feature(
    request: Request,
    feature_id: int
):
    """
    Создать задачи для фичи (вызов Architect).
    
    Args:
        request: HTTP запрос
        feature_id: ID фичи
        
    Returns:
        PlanResponse: Информация о созданных задачах
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        feature_id=feature_id
    )
    
    try:
        # Получаем фичу из базы данных
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, status FROM features WHERE id = :id"),
                {"id": feature_id}
            )
            feature_row = result.fetchone()
            
            if not feature_row:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(
                    request,
                    correlation_id,
                    status_code=404,
                    duration_ms=duration_ms,
                    error_code="FEATURE_NOT_FOUND"
                )
                
                raise HTTPException(
                    status_code=404,
                    detail="Feature not found",
                    headers={"error_code": "FEATURE_NOT_FOUND"}
                )
            
            # Проверяем статус фичи
            if feature_row[1] != 'NEW':
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(
                    request,
                    correlation_id,
                    status_code=400,
                    duration_ms=duration_ms,
                    error_code="INVALID_FEATURE_STATUS"
                )
                
                raise HTTPException(
                    status_code=400,
                    detail="Feature is not in NEW status",
                    headers={"error_code": "INVALID_FEATURE_STATUS"}
                )
            
            # В реальной реализации здесь будет вызов Architect для генерации плана
            # Для демонстрации создаем простой план
            
            # Создаем задачи для фичи
            roles = ["Dev", "QA", "Scribe"]  # Простой пример ролей
            created_tasks = []
            
            for role in roles:
                result = conn.execute(
                    text("""
                        INSERT INTO tasks (
                            feature_id, role, status, attempts, scheduled_at
                        ) VALUES (
                            :feature_id, :role, 'NEW', 0, datetime('now')
                        )
                    """),
                    {
                        "feature_id": feature_id,
                        "role": role
                    }
                )
                
                task_id = result.lastrowid
                
                # Получаем созданную задачу
                result = conn.execute(
                    text("SELECT id, role, status FROM tasks WHERE id = :id"),
                    {"id": task_id}
                )
                task_row = result.fetchone()
                
                if task_row:
                    created_tasks.append(
                        TaskPlanResponse(
                            id=task_row[0],
                            role=task_row[1],
                            status=task_row[2]
                        )
                    )
            
            # Обновляем статус фичи
            conn.execute(
                text("""
                    UPDATE features 
                    SET status = 'PLANNED'
                    WHERE id = :id
                """),
                {"id": feature_id}
            )
            
            conn.commit()
            
            # Создаем пустой package_contract для демонстрации
            package_contract = {
                "feature_id": feature_id,
                "version": "1.0",
                "description": "Auto-generated package contract"
            }
            
            # Логируем успешное завершение вызова
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                feature_id=feature_id,
                tasks_created=len(created_tasks)
            )
            
            return PlanResponse(
                feature_id=feature_id,
                tasks=created_tasks,
                package_contract=package_contract
            )
            
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to plan feature: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.post("/features/{feature_id}/run",
             response_model=RunResponse,
             responses={
                 400: {"model": ErrorResponse},
                 404: {"model": ErrorResponse}
             })
async def run_feature(
    request: Request,
    feature_id: int
):
    """
    Запустить/резюмировать G1 (Dev→Gate→QA→Scribe→Apply).
    
    Args:
        request: HTTP запрос
        feature_id: ID фичи
        
    Returns:
        RunResponse: Информация о запуске
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        feature_id=feature_id
    )
    
    try:
        # Получаем фичу из базы данных
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, status FROM features WHERE id = :id"),
                {"id": feature_id}
            )
            feature_row = result.fetchone()
            
            if not feature_row:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(
                    request,
                    correlation_id,
                    status_code=404,
                    duration_ms=duration_ms,
                    error_code="FEATURE_NOT_FOUND"
                )
                
                raise HTTPException(
                    status_code=404,
                    detail="Feature not found",
                    headers={"error_code": "FEATURE_NOT_FOUND"}
                )
            
            # Проверяем статус фичи
            if feature_row[1] not in ['PLANNED', 'RUNNING']:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(
                    request,
                    correlation_id,
                    status_code=400,
                    duration_ms=duration_ms,
                    error_code="INVALID_FEATURE_STATUS"
                )
                
                raise HTTPException(
                    status_code=400,
                    detail="Feature is not in PLANNED or RUNNING status",
                    headers={"error_code": "INVALID_FEATURE_STATUS"}
                )
            
            # Генерируем run_id
            run_id = str(uuid.uuid4())
            
            # В реальной реализации здесь будет запуск/резюмирование графа G1
            # Для демонстрации просто обновляем статус фичи и создаем запись в graph_runs
            
            # Создаем запись в graph_runs
            conn.execute(
                text("""
                    INSERT INTO graph_runs (
                        run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at
                    ) VALUES (
                        :run_id, :feature_id, 'G1', :thread_id, :state_json, 'RUNNING', datetime('now')
                    )
                """),
                {
                    "run_id": run_id,
                    "feature_id": feature_id,
                    "thread_id": str(uuid.uuid4()),
                    "state_json": json.dumps({"state": "started"})
                }
            )
            
            # Обновляем статус фичи
            conn.execute(
                text("""
                    UPDATE features 
                    SET status = 'RUNNING'
                    WHERE id = :id
                """),
                {"id": feature_id}
            )
            
            # Обновляем статус всех задач фичи
            conn.execute(
                text("""
                    UPDATE tasks 
                    SET status = 'RUNNING', started_at = datetime('now')
                    WHERE feature_id = :feature_id AND status = 'NEW'
                """),
                {"feature_id": feature_id}
            )
            
            conn.commit()
            
            # Логируем успешное завершение вызова
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                feature_id=feature_id,
                run_id=run_id
            )
            
            return RunResponse(
                run_id=run_id,
                state="STARTED"
            )
            
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to run feature: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/graph/{run_id}/status",
            response_model=GraphStatusResponse,
            responses={
                404: {"model": ErrorResponse}
            })
async def get_graph_status(
    request: Request,
    run_id: str
):
    """
    Получить статус выполнения графа.
    
    Args:
        request: HTTP запрос
        run_id: ID запуска графа
        
    Returns:
        GraphStatusResponse: Статус графа
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        run_id=run_id
    )
    
    try:
        # Получаем статус графа из базы данных
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at 
                    FROM graph_runs 
                    WHERE run_id = :run_id
                """),
                {"run_id": run_id}
            )
            graph_row = result.fetchone()
            
            if not graph_row:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call_end(
                    request,
                    correlation_id,
                    status_code=404,
                    duration_ms=duration_ms,
                    error_code="GRAPH_RUN_NOT_FOUND"
                )
                
                raise HTTPException(
                    status_code=404,
                    detail="Graph run not found",
                    headers={"error_code": "GRAPH_RUN_NOT_FOUND"}
                )
            
            # Преобразуем результат в словарь
            last_checkpoint = ""
            if graph_row[6]:
                # Преобразуем datetime в строку
                if hasattr(graph_row[6], 'isoformat'):
                    last_checkpoint = graph_row[6].isoformat()
                else:
                    last_checkpoint = str(graph_row[6])
            
            # Логируем успешное завершение вызова
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=200,
                duration_ms=duration_ms,
                run_id=run_id,
                status=graph_row[5]
            )
            
            return GraphStatusResponse(
                run_id=graph_row[0],
                graph="G1",  # Всегда G1 согласно спецификации
                status=graph_row[5] or "UNKNOWN",
                last_checkpoint=last_checkpoint
            )
            
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get graph status: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )
```

---

## Файл: tests/test_orchestrator_api_v2.py

```python
import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
import os
import tempfile
import sqlite3


class TestOrchestratorAPIV2(unittest.TestCase):
    """Тесты для новой версии API оркестратора, соответствующей спецификации API-Orchestrator-001.md."""

    def setUp(self):
        """Подготовка к тестам."""
        # Создаем временную базу данных для тестов
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.database_url = f"sqlite:///{self.temp_db_path}"
        
        # Устанавливаем переменную окружения для тестовой базы данных
        os.environ['DATABASE_URL'] = self.database_url
        os.environ['ENV'] = 'test'
        
        # Создаем таблицы в тестовой базе данных
        self._create_test_tables()
        
        # Создаем клиента для тестирования
        self.client = TestClient(app)

    def tearDown(self):
        """Очистка после тестов."""
        # Закрываем файл базы данных и удаляем его
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
        
        # Убираем переменную окружения
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

    def _create_test_tables(self):
        """Создает тестовые таблицы в базе данных."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        # Создаем таблицы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                intent_json TEXT,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                env TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                dsl_json TEXT,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                budget_tokens INTEGER,
                scheduled_at DATETIME,
                started_at DATETIME,
                finished_at DATETIME
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_runs (
                run_id TEXT PRIMARY KEY,
                feature_id INTEGER NOT NULL,
                graph_name TEXT NOT NULL,
                thread_id TEXT,
                state_json TEXT,
                status TEXT,
                last_checkpoint_at DATETIME
            )
        """)
        
        conn.commit()
        conn.close()

    def test_create_feature_success(self):
        """Тест успешного создания фичи."""
        # Подготавливаем данные для запроса
        feature_data = {
            "title": "Test Feature",
            "intent": {"action": "test", "params": {}}
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("id", response_data)
        self.assertIn("status", response_data)
        self.assertEqual(response_data["status"], "NEW")
        
        # Проверяем, что фича действительно создалась в базе
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, status FROM features WHERE title = ?", ("Test Feature",))
        feature_row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(feature_row)
        self.assertEqual(feature_row[1], "Test Feature")
        self.assertEqual(feature_row[2], "NEW")

    def test_create_feature_idempotency(self):
        """Тест идемпотентности создания фичи."""
        # Подготавливаем данные для запроса
        feature_data = {
            "title": "Idempotent Feature",
            "intent": {"action": "test", "params": {}}
        }
        
        # Отправляем первый POST запрос
        response1 = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response1.status_code, 200)
        response1_data = response1.json()
        feature_id_1 = response1_data["id"]
        
        # Отправляем второй POST запрос с теми же данными
        response2 = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(response2.status_code, 200)
        response2_data = response2.json()
        feature_id_2 = response2_data["id"]
        
        # Проверяем, что вернулся тот же ID
        self.assertEqual(feature_id_1, feature_id_2)
        self.assertEqual(response1_data["status"], response2_data["status"])

    def test_plan_feature_success(self):
        """Тест успешного планирования фичи."""
        # Сначала создаем фичу
        feature_data = {
            "title": "Feature to Plan",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        # Отправляем POST запрос для генерации плана
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("feature_id", response_data)
        self.assertIn("tasks", response_data)
        self.assertIn("package_contract", response_data)
        self.assertEqual(response_data["feature_id"], feature_id)
        
        # Проверяем, что созданы задачи
        self.assertGreater(len(response_data["tasks"]), 0)
        for task in response_data["tasks"]:
            self.assertIn("id", task)
            self.assertIn("role", task)
            self.assertIn("status", task)
            self.assertEqual(task["status"], "NEW")
        
        # Проверяем, что статус фичи обновился
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
        feature_row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(feature_row)
        self.assertEqual(feature_row[0], "PLANNED")

    def test_plan_feature_not_found(self):
        """Тест планирования несуществующей фичи."""
        # Отправляем POST запрос для генерации плана несуществующей фичи
        response = self.client.post("/api/v1/orchestrator/features/99999/plan")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 404)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("error_code", response_data)
        self.assertEqual(response_data["error_code"], "FEATURE_NOT_FOUND")

    def test_plan_feature_invalid_status(self):
        """Тест планирования фичи с недопустимым статусом."""
        # Сначала создаем фичу
        feature_data = {
            "title": "Feature to Plan",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        # Обновляем статус фичи на PLANNED вручную
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE features SET status = 'PLANNED' WHERE id = ?", (feature_id,))
        conn.commit()
        conn.close()
        
        # Пытаемся снова запланировать фичу
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 400)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("error_code", response_data)
        self.assertEqual(response_data["error_code"], "INVALID_FEATURE_STATUS")

    def test_run_feature_success(self):
        """Тест успешного запуска фичи."""
        # Сначала создаем фичу
        feature_data = {
            "title": "Feature to Run",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        # Планируем фичу
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        # Отправляем POST запрос для запуска фичи
        response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("run_id", response_data)
        self.assertIn("state", response_data)
        self.assertEqual(response_data["state"], "STARTED")
        
        # Проверяем, что статус фичи обновился
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
        feature_row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(feature_row)
        self.assertEqual(feature_row[0], "RUNNING")

    def test_run_feature_not_found(self):
        """Тест запуска несуществующей фичи."""
        # Отправляем POST запрос для запуска несуществующей фичи
        response = self.client.post("/api/v1/orchestrator/features/99999/run")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 404)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("error_code", response_data)
        self.assertEqual(response_data["error_code"], "FEATURE_NOT_FOUND")

    def test_get_graph_status_success(self):
        """Тест успешного получения статуса графа."""
        # Сначала создаем фичу и запускаем её
        feature_data = {
            "title": "Feature for Graph Status",
            "intent": {"action": "test", "params": {}}
        }
        
        create_response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        self.assertEqual(create_response.status_code, 200)
        feature_id = create_response.json()["id"]
        
        plan_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/plan")
        self.assertEqual(plan_response.status_code, 200)
        
        run_response = self.client.post(f"/api/v1/orchestrator/features/{feature_id}/run")
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]
        
        # Отправляем GET запрос для получения статуса графа
        response = self.client.get(f"/api/v1/orchestrator/graph/{run_id}/status")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("run_id", response_data)
        self.assertIn("graph", response_data)
        self.assertIn("status", response_data)
        self.assertIn("last_checkpoint", response_data)
        self.assertEqual(response_data["run_id"], run_id)
        self.assertEqual(response_data["graph"], "G1")
        self.assertEqual(response_data["status"], "RUNNING")

    def test_get_graph_status_not_found(self):
        """Тест получения статуса несуществующего графа."""
        # Отправляем GET запрос для получения статуса несуществующего графа
        response = self.client.get("/api/v1/orchestrator/graph/nonexistent-run-id/status")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 404)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("error_code", response_data)
        self.assertEqual(response_data["error_code"], "GRAPH_RUN_NOT_FOUND")

    def test_api_routes_exist(self):
        """Тест наличия всех маршрутов API."""
        # Проверяем, что маршруты существуют
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/orchestrator/features",
            "/api/v1/orchestrator/features/{feature_id}/plan",
            "/api/v1/orchestrator/features/{feature_id}/run",
            "/api/v1/orchestrator/graph/{run_id}/status"
        ]
        
        for route in expected_routes:
            # Проверяем, что маршрут существует (без учета параметров пути)
            route_base = route.split("/{")[0] if "/{" in route else route
            found = any(r.startswith(route_base) for r in routes)
            self.assertTrue(found, f"Route {route} should exist")

    @patch('app.api.orchestrator_v2.log.info')
    def test_api_logging(self, mock_log_info):
        """Тест логирования API вызовов."""
        # Подготавливаем данные для запроса
        feature_data = {
            "title": "Logging Test Feature",
            "intent": {"action": "test", "params": {}}
        }
        
        # Отправляем POST запрос
        response = self.client.post("/api/v1/orchestrator/features", json=feature_data)
        
        # Проверяем, что логирование вызывалось
        self.assertTrue(mock_log_info.called)
        
        # Проверяем, что логи содержат нужные события
        log_calls = [call for call in mock_log_info.call_args_list 
                    if 'event' in call.kwargs and call.kwargs['event'] in ['api_call_start', 'api_call_end']]
        self.assertGreater(len(log_calls), 0)


if __name__ == '__main__':
    unittest.main()
```
## Файл: CHANGELOG.md
## Файл: docs/UI-000.md
# UI-000: Админка (MVP)

## Общее описание

Админка для управления системой Feature Factory с веб-интерфейсом, предоставляющая удобный способ просмотра состояния системы, управления фичами, задачами, запусками графов, логами и документацией.

## Стек технологий (MVP)

- Фронтенд: Vite + React + TypeScript + Tailwind + shadcn/ui (Radix)
- Управление состоянием: TanStack Query
- Потоки данных: EventSource (SSE) для стриминга логов/статусов
- Сборка: статические файлы, served через Nginx
- Безопасность: BasicAuth на домене

## Навигация и экраны

### Dashboard (по умолчанию)

Карточки:
- System Health (api/health, env)
- Backlog (features NEW/PLANNED)
- Runs (graph_runs последние N)
- LLM Budgets (сводка/день)
- Errors (последние ERROR из logs)
- Docs (doc_registry summary)

Banner ENV: TEST

### Features / Backlog

Список фич (title, status, priority, created_at, env).

Действия: Plan, Run, Pause, Retry, Promote (пока выключено).

Деталь: фича → задачи (tasks) + текущий run_id, история.

### Tasks

Последние задачи (role, status, attempts, started/finished). Фильтры по role/status.

### Runs (Graph)

Последние graph_runs; статус по run_id; кнопка Resume если прервано.

### Logs (tail)

Поток JSON логов с фильтрами (component/level/event/agent_role). Автопрокрутка; пауза; копирование записи.

### Tokens

/admin/tokens — сводка расхода токенов (день/роль/модель).

### Docs

doc_registry: список документов, версия, hash, updated_at; кнопка Docs Rebuild.

### Settings

Просмотр settings (read-only в MVP): APP_TZ, расписания, IDs.

### Chat (Maintainer)

Поле ввода NL → preview intent/DAG; кнопки Создать фичу, Сразу выполнить.

## Маршрутизация фронта

Публичный путь: / → Dashboard.

Базовый префикс API: /api/v1 (конфигурируется через VITE_API_BASE_URL).

Защита: весь /ui/* и / под BasicAuth на уровне Nginx.

## Дизайн и компоненты

Библиотека: shadcn/ui (на базе Radix) под Tailwind; иконки lucide.

Компоненты:
- AppShell (Sidebar + Header + Main + Toaster)
- DataTable (таблицы для Features/Tasks/Tokens с пагинацией/фильтрами)
- LogViewer (моноширинный, поиск, авто-скролл, цвет уровней)
- StatusPill (DONE/FAILED/RETRYABLE_ERROR/NEW/RUNNING)
- CodeBlock (подсветка для JSON/Markdown)
- ChatPane (история, ввод, отправка, превью DAG)

## Потоки данных (клиент)

Клиент HTTP: fetch + TanStack Query (кеш/рефетч/ошибки).

Real-time: SSE GET /api/v1/stream/events с типами: job_started|job_finished|error|index_updated|doc_updated|llm_call_end. Fallback: опрос /api/v1/logs?since=....

Ошибки: глобальный обработчик — toast + запись в консоль.

## Новые API (для UI + NL)

POST /api/v1/maintainer/intent — { nl_text } → { intent_json, issues[], suggestions[] }

POST /api/v1/maintainer/plan — { intent_json } → { dag: TaskDSL[], package_contract }

POST /api/v1/orchestrator/features (уже есть) — расширить: поддержка intent_json и авто-Plan.

GET /api/v1/stream/events — SSE.

GET /api/v1/logs/tail — последние N записей (fallback для UI).

## Статика и деплой

Проект UI в app/ui/.

Сборка vite build → app/ui/dist/.

Nginx (тест):
```
location / { 
  root /opt/feature-factory/app/ui/dist; 
  try_files $uri /index.html; 
}

BasicAuth включён; прокси на /api/ как сейчас.

Кеш: immutable для assets/* (365д), no-store для index.html.
```

## Схема файлов фронта

```
app/ui/
  package.json
  vite.config.ts
  index.html
  src/
    main.tsx
    app.css
    lib/
      api.ts            # base fetcher + QueryClient
      sse.ts            # EventSource helper
      types.ts          # DTO & enums (Status, Role, etc.)
      format.ts         # форматтеры дат/статусов
    state/
      uiStore.ts        # мелкие флаги/фильтры (Zustand)
    components/
      AppShell.tsx
      StatusPill.tsx
      DataTable.tsx
      LogViewer.tsx
      ChatPane.tsx
    pages/
      Dashboard.tsx
      Features.tsx
      FeatureDetail.tsx
      Tasks.tsx
      Runs.tsx
      Logs.tsx
      Tokens.tsx
      Docs.tsx
      Settings.tsx
    routes.tsx          # router
    shadcn/             # сгенерённые компоненты
    assets/
```

## Статусы/словари (UI)

FeatureStatus: NEW | PLANNED | RUNNING | DONE | FAILED

TaskStatus: NEW | RUNNING | DONE | RETRYABLE_ERROR | FAILED | WAIT_BUDGET

Role: Architect | Dev | QA | Scribe | Maintainer

## Схема SSE событий

События, передаваемые через SSE:
- job_started
- job_finished
- error
- index_updated
- doc_updated
- llm_call_end

## DTO (Data Transfer Objects)

### Feature

```json
{
  "id": "integer",
  "title": "string",
  "intent_json": "object or null",
  "status": "NEW | PLANNED | RUNNING | DONE | FAILED",
  "priority": "integer",
  "created_at": "datetime",
  "created_by": "string",
  "env": "string"
}
```

### Task

```json
{
  "id": "integer",
  "feature_id": "integer",
  "role": "Architect | Dev | QA | Scribe | Maintainer",
  "dsl_json": "object",
  "status": "NEW | RUNNING | DONE | RETRYABLE_ERROR | FAILED | WAIT_BUDGET",
  "attempts": "integer",
  "budget_tokens": "integer",
  "scheduled_at": "datetime",
  "started_at": "datetime",
  "finished_at": "datetime"
}
```

### GraphRun

```json
{
  "run_id": "string",
  "feature_id": "integer",
  "graph_name": "string",
  "thread_id": "string",
  "state_json": "object",
  "status": "RUNNING | DONE | FAILED",
  "last_checkpoint_at": "datetime"
}
```

### LogEntry

```json
{
  "ts": "datetime",
  "level": "string",
  "env": "string",
  "component": "string",
  "agent_role": "string",
  "run_id": "string",
  "task_id": "string",
  "correlation_id": "string",
  "event": "string",
  "kv": "object"
}
```

### TokenUsage

```json
{
  "role": "string",
  "model": "string",
  "input_tokens": "integer",
  "output_tokens": "integer",
  "total_tokens": "integer",
  "cost": "number"
}
```

### DocRegistryEntry

```json
{
  "doc_name": "string",
  "version": "string",
  "content_hash": "string",
  "updated_at": "datetime"
}
```

### MaintainerIntent

```json
{
  "nl_text": "string",
  "intent_json": "object",
  "issues": "array of strings",
  "suggestions": "array of strings"
}
```

### MaintainerPlan

```json
{
  "intent_json": "object",
  "dag": "array of TaskDSL",
  "package_contract": "object"
}
```
## Файл: docs/Commands-UI-000.md
# Commands-UI-000: Команды админки

## Общее описание

Документ описывает команды, доступные в веб-интерфейсе админки Feature Factory.

## Навигация

### Dashboard
- Просмотр карточек System Health, Backlog, Runs, LLM Budgets, Errors, Docs
- ENV banner показывает текущее окружение (TEST)

### Features / Backlog
- Просмотр списка фич с фильтрацией по статусу
- Действия с фичами:
  - Plan: запланировать выполнение фичи
  - Run: запустить выполнение фичи
  - Pause: приостановить выполнение фичи (временно недоступно)
  - Retry: повторить выполнение фичи
  - Promote: продвинуть фичу (временно недоступно)
- Просмотр деталей фичи:
  - Список задач
  - Текущий run_id
  - История выполнения

### Tasks
- Просмотр списка последних задач
- Фильтрация по роли и статусу
- Просмотр деталей задачи

### Runs (Graph)
- Просмотр списка последних запусков графов
- Просмотр статуса конкретного запуска по run_id
- Кнопка Resume для возобновления прерванного запуска

### Logs (tail)
- Просмотр потока логов в реальном времени
- Фильтрация логов по компоненту, уровню, событию, роли агента
- Автопрокрутка к последним записям
- Пауза потока логов
- Копирование отдельных записей логов

### Tokens
- Просмотр сводки расхода токенов по дням, ролям и моделям

### Docs
- Просмотр списка документов из реестра
- Просмотр версии, хэша и даты обновления каждого документа
- Кнопка Docs Rebuild для пересборки документации

### Settings
- Просмотр настроек системы (только чтение):
  - APP_TZ (часовой пояс приложения)
  - Расписания
  - Идентификаторы систем

### Chat (Maintainer)
- Ввод команд на естественном языке
- Предпросмотр сгенерированного intent и DAG
- Кнопки:
  - Создать фичу: создает новую фичу на основе введенного описания
  - Сразу выполнить: немедленно выполняет команду (если возможно)

## API Endpoints

### Orchestrator

POST /api/v1/orchestrator/features
- Создание новой фичи
- Параметры: title, intent_json
- Ответ: id, status

POST /api/v1/orchestrator/features/{id}/plan
- Планирование выполнения фичи
- Ответ: список задач, package_contract

POST /api/v1/orchestrator/features/{id}/run
- Запуск выполнения фичи
- Ответ: run_id, state

GET /api/v1/orchestrator/graph/{run_id}/status
- Получение статуса запуска графа
- Ответ: run_id, graph, status, last_checkpoint

### Index

GET /api/v1/index/symbol
- Получение информации о символе
- Параметры: name

GET /api/v1/index/calls
- Получение информации о вызовах функции
- Параметры: name

### Tokens

GET /admin/tokens
- Получение сводки расхода токенов
- Ответ: сводка по ролям, моделям, дням

### Logs

GET /api/v1/logs/tail
- Получение последних записей логов (fallback для UI)
- Параметры: limit (по умолчанию 100)

### Stream

GET /api/v1/stream/events
- SSE поток событий
- События: job_started, job_finished, error, index_updated, doc_updated, llm_call_end

### Maintainer

POST /api/v1/maintainer/intent
- Генерация intent из естественного языка
- Параметры: nl_text
- Ответ: intent_json, issues, suggestions

POST /api/v1/maintainer/plan
- Генерация плана выполнения из intent
- Параметры: intent_json
- Ответ: dag, package_contract## Файл: CHANGELOG.md

# CHANGELOG

## [Unreleased]

### Added
- Инициализация Alembic и создание первой миграции (0001_init) для создания всех базовых таблиц MVP.
- Добавлены тесты для проверки миграций и их идемпотентности.
- Обновлена документация по архитектуре и схеме базы данных.

### Changed
- Обновлена версия капсулы контекста до v1.1 (E7-CAPSULE-UPDATE)
- Добавлены новые разделы в капсулу: DB, Paths, Tests, LLM
- Добавлены политики db_policy_violation и qa_policy_violation в ChangePolicy-000.md

### Indexer
- Новая миграция Alembic: code_registry, symbol_index, call_graph_edges
- Скрипт scripts/update_code_registry.py для индексации кода
- API: GET /api/v1/index/symbol, /api/v1/index/calls
- Unit-тесты для парсинга JSONL ctags и DOT pyan3
- Документация: Architecture.md (раздел Indexer), ChangePolicy-000.md (событие index_updated)

### Logging
- Добавлены декораторы логирования: `@log_job`, `@log_http`, `@log_db`
- Добавлен middleware для корреляции запросов: `CorrelationIdMiddleware`
- Обновлена документация: Logging-001.md (версия 1.2), Architecture.md (раздел "Логи и корреляция")
- Добавлены unit-тесты для проверки логирования

### Admin UI
- Добавлена админка с BasicAuth: `/admin`
- SQLAdmin интерфейс: `/admin/sqladmin`
- Jobs view: таблица задач
- Logs tail: фильтрация логов
- Docs status: статус документов
- NL форма: POST текст → вызов Maintainer (LLM) → показ intent/DAG (read-only)
- X-Request-ID в ответах для корреляции
- Обновлена документация: Architecture.md (раздел "Admin/UI и NL-flow"), Commands-NL.md

### Stack Alignment
- Обновлена app/agents/prompts/_capsule.md: Python 3.11 как базовый, допускается 3.12 на MVP (фикс ADR)
- Добавлен docs/ADR-002-python-version.md: текущее исполнение 3.12; план перехода при необходимости
- Обновлены ссылки на Logging-001, Policy-LLM, Project-Reference

### Orchestrator Gate
- Добавлен docs/Artifact-Manifest.md: описание формата artifact manifest
- Добавлен docs/package_contract.schema.json: JSON schema для валидации package contracts
- Реализован app/orchestrator/gates.py: валидация artifact manifests и package contracts
- Реализован app/orchestrator/apply.py: применение артефактов, запуск AutoIndex и DocSync
- Добавлены тесты: tests/test_orchestrator_gate.py
- Обновлена документация: ChangePolicy-000.md (событие artifact_rejected), Architecture.md (раздел "Pipeline")
- Улучшена валидация: отсутствующий manifest → REJECT, невалидный manifest → REJECT, отсутствующий package_contract в задачах Architect → REJECT
- При apply: AutoIndex и DocSync триггерятся корректно
- Обновлены политики в ChangePolicy-000.md: добавлены события artifact_applied и doc_updated

### LLM Budgets
- Обновлён Policy-LLM-000.md: маршрутизация Flash→Qwen→wait; Architect→Claude/GPT при наличии квот
- Определены дневные лимиты и пороги на роль (Architect/Dev/QA/Scribe)
- Добавлена матрица таймаутов/ретраев (LLM/HTTP)
- Настроен LiteLLM proxy с конфигурацией маршрутизации
- Добавлены конфигурационные файлы для LiteLLM
- Реализован учет токенов по ролям и моделям
- Добавлен endpoint /admin/tokens для просмотра статистики токенов

### LLM Router (CLI-first)
- Реализован новый транспорт для взаимодействия с LLM через CLI
- Добавлена поддержка роутинга по ролям с fallback'ами между провайдерами
- Dev/QA/Scribe: qwen → gemini
- Architect/Maintainer: claude → gpt → gemini
- Реализована проверка бюджетов токенов перед вызовом LLM
- Добавлены конфигурационные файлы для роутинга и CLI команд
- Обновлена документация: Policy-LLM-000.md, Architecture.md

### LLM Tokens and Budgets (CLI)
- Расширена система учета токенов для CLI-вызовов
- Добавлена оценка количества токенов перед вызовом
- Реализована проверка бюджетов токенов по ролям
- Добавлена запись фактического использования токенов после вызова
- Обновлен endpoint /admin/tokens для отображения актуальной статистики
- Добавлены unit-тесты для проверки функциональности

### Database Guard
- Реализована защита путей к БД для TEST и PROD окружений
- Добавлена проверка соответствия путей: TEST → `/opt/feature-factory/data/test.db`, PROD → `/opt/feature-factory/data/prod.db`
- При несовпадении пути выбрасывается исключение `FAILED_NEEDS_ATTENTION`
- Ошибки логируются с типом `err_type=DbPathMismatch`
- Добавлены unit-тесты для проверки функциональности

### LangGraph Orchestration
- Подключена библиотека LangGraph для оркестрации
- Реализован чекпоинтер SQLite для сохранения состояния графа (`/opt/feature-factory/data/checkpoints.db`)
- Создан каркас графа G1 с узлами-заглушками (Dev→Gate→QA→Scribe→Apply)
- Добавлены функции управления запуском: `start_run(feature_id)`, `resume_run(run_id)`
- Реализованы типы контекста узлов: `RunCtx` с полями `run_id`, `feature_id`, `task_id`, `correlation_id`, `env`
- Добавлено логирование событий графа: `job_started/finished`, `retry_scheduled`
- Добавлены unit-тесты для проверки функциональности

### LangGraph Real Nodes
- Реализованы реальные узлы графа G1:
  - Dev: Генерирует код с помощью LLM роутера
  - Gate: Валидирует артефакты и контракты (интеграция с существующим оркестратором)
  - QA: Запускает тесты для артефактов
  - Scribe: Обновляет документацию
  - Apply: Применяет артефакты (интеграция с существующим оркестратором)
- Каждый узел идемпотентен и логирует `correlation_id`
- При `RETRYABLE_ERROR` выполняется backoff из капсулы
- Добавлен e2e тест для прогона пустой фичи: Dev→Gate→QA→Scribe→Apply→AutoIndex/DocSync
- Обновлена документация: Architecture.md, CHANGELOG.md

### Backlog Schema
- Добавлены таблицы для поддержки backlog-а:
  - `features`: Хранит информацию о фичах (id, title, intent_json, status, priority, created_at, created_by, env)
  - `tasks`: Хранит задачи для фич (id, feature_id, role, dsl_json, status, attempts, budget_tokens, scheduled_at, started_at, finished_at)
  - `graph_runs`: Хранит информацию о запусках графов (run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at)
- Создана миграция Alembic для добавления таблиц
- Добавлены уникальные индексы и внешние ключи
- Миграции идемпотентны
- Добавлены unit-тесты для проверки структуры таблиц
- Обновлена документация: Schema-000-base-tables.md, CHANGELOG.md

### Orchestration Loop
- Реализован цикл "самовыполнения" из бэклога
- Создан планировщик `app/orchestrator/loop.py`:
  - Обрабатывает `features.NEW` каждые N секунд
  - Вызывает Architect для генерации плана, если он отсутствует
  - Создает `tasks.NEW` на основе плана
  - Запускает/резюмирует граф G1 для готовых задач
  - Обрабатывает состояние `WAIT_BUDGET` для отложенных задач
  - Поддерживает механизм повторных попыток при ошибках
- Добавлены unit-тесты для проверки функциональности
- Обновлена документация: Architecture.md, CHANGELOG.md

### Orchestration API
- Реализован REST API для интеграции с UI и скриптами:
  - `POST /api/v1/orchestrator/features` — создать фичу (Maintainer)
  - `POST /api/v1/orchestrator/features/{id}/plan` — Architect → DAG/DSL + package_contract → tasks
  - `POST /api/v1/orchestrator/features/{id}/run` — запустить/резюмировать G1
  - `GET /api/v1/orchestrator/graph/{run_id}/status` — статус узлов/чекпоинтов
- Все вызовы API логируются с `api_call_start/end`
- Добавлены unit-тесты для проверки функциональности
- Обновлена документация: Architecture.md, CHANGELOG.md

### Orchestrator API v2 (E7-ORCH-API-DEV)
- Реализован новый REST API оркестратора согласно спецификации API-Orchestrator-001.md:
  - `POST /api/v1/orchestrator/features` с идемпотентностью по (title, env)
  - `POST /api/v1/orchestrator/features/{id}/plan` для создания задач
  - `POST /api/v1/orchestrator/features/{id}/run` для запуска графа
  - `GET /api/v1/orchestrator/graph/{run_id}/status` для получения статуса графа
- Все эндпоинты строго следуют спецификации с валидацией через Pydantic схемы
- Добавлены JSON Schema для всех ответов API
- Реализована строгая обработка кодов ответов: успех=200, ошибки=400/404/409
- Все вызовы API логируются с использованием logging_helpers
- Добавлены unit-тесты с полным покрытием функциональности
- Обновлена документация: API-Orchestrator-001.md, Architecture.md, CHANGELOG.md

### Domains and HTTPS
- Добавлены конфигурационные файлы Nginx для доменов etl-tst.chococraft.ru (8081) и etl.chococraft.ru (8080)
- Добавлены systemd сервисы для test и prod окружений
- Добавлены файлы окружения /etc/default/feature-factory-prod и /etc/default/feature-factory-test
- Добавлен скрипт setup_domains_https.sh для автоматической настройки
- Добавлен скрипт check_domains.sh для проверки доступности доменов
- Обеспечена проксидка X-Request-ID через заголовки
- Настроена BasicAuth защита для /admin endpoints

# CHANGELOG

## [Unreleased]

### Added
- Инициализация Alembic и создание первой миграции (0001_init) для создания всех базовых таблиц MVP.
- Добавлены тесты для проверки миграций и их идемпотентности.
- Обновлена документация по архитектуре и схеме базы данных.

### Indexer
- Новая миграция Alembic: code_registry, symbol_index, call_graph_edges
- Скрипт scripts/update_code_registry.py для индексации кода
- API: GET /api/v1/index/symbol, /api/v1/index/calls
- Unit-тесты для парсинга JSONL ctags и DOT pyan3
- Документация: Architecture.md (раздел Indexer), ChangePolicy-000.md (событие index_updated)

---
