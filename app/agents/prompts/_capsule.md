# КАПСУЛА КОНТЕКСТА v1.1 — Фабрика бизнес‑фич (MVP)

## Инварианты
- Один VPS; окружения: **test (8081, DRY_RUN=true, без APScheduler)** / **prod (8080, DRY_RUN=false)**.
- Стек: FastAPI; SQLite+SQLAlchemy+Alembic; APScheduler; httpx(+tenacity); sqladmin; structlog; LangGraph; LiteLLM.
- **Python 3.11 как базовый, допускается 3.12 на MVP (фикс ADR)**, стиль PEP8, типы обязательны; докстринги Google-style.
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

## DB

Единственный источник правды для БД: DATABASE_URL из env. Запрещено конструировать пути/имена БД в коде/тестах.

Для test-окружения Orchestrator устанавливает DATABASE_URL=file:/opt/feature-factory/tmp/test.db (или sqlite:////opt/feature-factory/tmp/test.db).

Запрещено: создавать новые файлы БД (напр. test.newdb). Gate=>artifact_rejected(db_policy_violation).

Migrations: любые тесты гоняют Alembic на той БД, что в DATABASE_URL. Никаких in-memory (:memory:) — запрещено.

## Paths

(Раздел будет заполнен позже, если потребуется)

## Tests

QA-общее: тесты обязаны проверять статусы/схемы/побочные эффекты; assertIn([200,404,500]) и пр. — запрещено.

## LLM

Router=CLI-first. Роутинг по ролям фиксирован (Dev/QA/Scribe→qwen→gemini; Architect/Maintainer→claude→gpt→gemini).