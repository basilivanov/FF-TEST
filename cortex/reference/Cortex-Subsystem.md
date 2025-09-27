# Cortex Subsystem — обзор и интеграция (TEST)

## Назначение
- Единый источник знаний для агентов и людей: доктрина, роли/политики, паттерны, справочники.
- Индекс кода и граф вызовов для точного контекста и навигации.
- Пакетирование контекста задач (ContextPackager) с приоритетами и фолбэками.
- Watchdog/самоисцеление как операционный контур вокруг пайплайна фич.

## Компоненты
- Документация (Cortex Docs)
  - Путь: `/opt/feature-factory/cortex/docs/**` (+ core/roles/patterns/reference)
  - Реестр: таблица `doc_registry` в БД (hash/version/updated_at)
  - API: `GET /api/v1/docs/status`, `POST /api/v1/docs/rebuild`
  - Инварианты: docsync_gated, файлы ≤ 200KB, валидная структура заголовков, JSON/схемы корректны

- Индекс кода и граф вызовов (Index Service)
  - БД индекса: `sqlite:////opt/feature-factory/data/index.db` (fallback на `DATABASE_URL`)
  - Таблицы: `symbol_index`, `call_graph_edges`
  - API: `GET /api/v1/index/symbol`, `GET /api/v1/index/calls`, `GET /api/v1/index/module-card`
  - События SSE: `index_updated` (прогресс индексации)

- ContextPackager (формирование контекстного пакета)
  - Модуль: `app/context/packager.py`
  - Приоритеты загрузки: core → role → patterns → reference → эвристики
  - Источники: Cortex V2 (`cortex/core/*`, `cortex/roles/*`, `cortex/patterns/*`) с fallback на старые пути
  - Расширение набора файлов по `call_graph_edges` и эвристикам; устойчивость к отсутствию индекса

- Watchdog (самоисцеление)
  - Политика: `configs/watchdog_policy.yaml` (SSoT → `/opt/feature-factory/configs/watchdog_policy.yaml`)
  - Узел графа: `app/graph/nodes/watchdog.py` → `watchdog_check_node`
  - Включение в G1: `app/graph/g1_feature.py` (после `dev` и перед `gate`)
  - События логов: `watchdog_triggered`, `task_escalated`, `dev_node_retry_with_context`

## Интеграция в Mission Control UI
- Dashboard
  - «Центр инцидентов»: агрегировать ошибки и `watchdog_*` из логов/SSE; быстрые действия (ретрай/эскалация)
  - «LLM ресурсы»: статусы провайдеров, тренды токенов, прогноз исчерпания
  - «Индекс/Документация»: виджеты актуальности (`docs/status`, `index_updated`), CTA «Пересобрать»

- Feature Detail
  - «Карта полёта»: DAG c состояниями узлов и метками Watchdog (переходы dev → watchdog → gate)
  - Панель узла: последние ошибки инструмента, решение Watchdog (`CONTINUE/ESCALATE_L1`), контекст эскалации
  - Хронолента: события `task_escalated`/`watchdog_triggered` рядом с Dev/Gate/QA

- Cortex Раздел (новый)
  - «Документация»: реестр `GET /api/v1/docs/status`, кнопка `POST /api/v1/docs/rebuild`
  - «Индекс»: поиск символов/модулей, карточки модулей, глубина графа вызовов
  - «Граф»: интерактивный CallGraph (фильтры source/target/file, подсветка ошибок)

## Контракты API (минимум для UI)
- Docs
  - `GET /api/v1/docs/status → {docs:[{doc_name,version,content_hash,updated_at}]}`
  - `POST /api/v1/docs/rebuild → {status,message,docs_updated}`
- Index
  - `GET /api/v1/index/calls?limit&offset&source_symbol&target_symbol&file_path → {edges,total,limit,offset,as_of,stale}`
  - `GET /api/v1/index/symbol?symbol_name&file_path → {symbols:[...]}`
  - `GET /api/v1/index/module-card?file_path → {module_card:{...}}`
- SSE
  - `GET /api/v1/stream/events` (типы: `job_started|job_finished|error|index_updated|doc_updated`)

## Наблюдаемость и безопасность
- Метрики: `runner_*`, `db_rw_ok`, `ui_bundle_hash`, ошибки UI: `ui_http_4xx_total`, `ui_http_5xx_total`
- Логи: маскирование секретов, corr_id_required, агрегация событий Watchdog
- Гардрейлы: UI вызывает только `/api/v1/*` и `/.well-known/ff-context.json`; отсутствие эндпоинта → graceful degradation

## DoD (для Cortex‑функций в UI)
- Дашборд показывает актуальность Docs/Index и события Watchdog (без обращения к `/orchestrator/*` напрямую)
- Раздел Cortex работает: список документов, поиск по индексу, визуализация графа
- SSE‑обновления не деградируют TTI/фреймрейт; ретраи с backoff

