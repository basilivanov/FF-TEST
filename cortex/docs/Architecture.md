# Architecture (MVP)
- Окружения: test (8081, DRY_RUN=true, без APScheduler), prod (8080, DRY_RUN=false).
- Роли: Maintainer (NL интерфейс), Architect, Dev, QA, Scribe, Orchestrator.
- Оркестрация: LangGraph; роутер LLM — CLI-first.
- Данные: SQLite, Alembic; JSON хранится в TEXT; взрыв JSON в Python.
- Индексация кода: scripts/index.sh → ctags (symbols), pyan3 (call-graph), module-cards; API `/api/v1/index/*`.
- Admin UI: Vite + React + TypeScript + Tailwind + shadcn/ui; API `/api/v1/*` и `/admin/*`.

## Admin/UI и NL-flow
- Maintainer API: `/api/v1/maintainer/*` — генерация intent и планов из NL
- Orchestrator API: `/api/v1/orchestrator/*` — управление фичами, задачами, запусками графов
- Stream API: `/api/v1/stream/events` — Server-Sent Events для реал-тайм обновлений
- Logs API: `/api/v1/logs/tail` — получение логов для fallback UI
- Tokens API: `/admin/tokens` — статистика расхода токенов
- Страницы админки: `/admin/agents`, `/admin/budget`, `/admin/call-graph`, `/admin/logs`
- NL-flow: UI Chat → Maintainer API (intent/plan) → Orchestrator API (features/tasks) → Graph execution
- UI Stack: Vite + React + TypeScript + Tailwind + shadcn/ui
- UI Components: AppShell, StatusPill, DataTable, LogViewer, CodeBlock, ChatPane
- State Management: Zustand для управления состоянием UI
- Data Fetching: TanStack Query для кэширования и управления запросами
- Real-time Updates: EventSource (SSE) для потока событий
- UI Testing: Jest + React Testing Library для модульных тестов

## База данных и миграции
- Используется Alembic для управления миграциями базы данных.
- Миграции хранятся в `app/db/migrations/versions`.
- Для применения миграций используется команда `alembic upgrade head`.
- **Стандартизированные пути к БД:**
  - TEST окружение: `sqlite:////opt/feature-factory/data/test.db`
  - PROD окружение: `sqlite:////opt/feature-factory/data/prod.db`
  - INDEX окружение: `sqlite:////opt/feature-factory/data/index.db`
- Защита путей к БД: `app/db/guard.py` проверяет соответствие путей для TEST и PROD окружений.
- Все компоненты используют переменную `DATABASE_URL` с корректными дефолтными значениями.

## Индексер кода
- Реестр кода: `code_registry` (файлы и их хэши)
- Индекс символов: `symbol_index` (классы, функции и другие символы)
- Граф вызовов: `call_graph_edges` (связи между символами)
- Инструменты: ctags (символы), pyan3 (граф вызовов)
- API: `/api/v1/index/symbol`, `/api/v1/index/calls`, `/api/v1/index/module-card`
- Pre-commit hook: автоматический запуск индексации при изменении Python файлов
- Сервис: `app/index/service.py` - централизованный сервис для работы с индексом кода

## Логи и корреляция
- Стандарт и профили — `docs/Logging-001.md`.
- Корреляция: `correlation_id` на вход HTTP/джоб; `run_id` — на конвейер.
- Инструментирование через `logging_helpers` декораторы.
- Middleware: `app/api/middleware.py` обеспечивает сквозную корреляцию запросов.
- Декораторы: `@log_job`, `@log_http`, `@log_db` для автоматического логирования операций.

## Pipeline (Gate→Apply→AutoIndex→DocSync)
- Gate: Orchestrator валидирует artifact_manifest и package_contract в ответах агентов
- Apply: Orchestrator применяет валидные артефакты
- AutoIndex: После apply запускается автоматическая индексация кода
- DocSync: После apply триггерится синхронизация документации

## LangGraph Orchestration
- Реализована оркестрация через LangGraph с поддержкой чекпоинтов
- Чекпоинты сохраняются в основной SQLite базе данных (используется `DATABASE_URL`)
- Граф G1 реализует pipeline: Dev→Gate→QA→Scribe→Apply
- Поддерживается возобновление прерванных запусков через `resume_run`
- Все узлы графа логируются с использованием `correlation_id`

## LangGraph Real Nodes
- Dev: Генерирует код с помощью LLM роутера
- Gate: Валидирует артефакты и контракты (интеграция с существующим оркестратором)
- QA: Запускает тесты для артефактов
- Scribe: Обновляет документацию
- Apply: Применяет артефакты и запускает AutoIndex/DocSync

## Orchestration: Router (CLI)
- Роутер LLM использует CLI-first транспорт для взаимодействия с провайдерами
- Поддерживается роутинг по ролям с fallback'ами между провайдерами
- Maintainer: qwen → gemini → stub
- Architect: anthropic_opus41 → openai_gpt5_via_codex → gemini_25_pro → qwen_code → stub
- Dev: qwen_code → gemini_25_flash → openai_gpt5_mini → stub
- QA: qwen_code → openai_gpt5_mini → gemini_25_flash → stub
- Scribe: qwen_code → openai_gpt5_mini → stub
- Реализована проверка бюджетов токенов перед вызовом LLM
- Все вызовы подробно логируются с указанием провайдера, модели и статистики использования
- Статистика использования токенов доступна через `/admin/tokens`
- Добавлена валидация путей CLI провайдеров для обеспечения безопасности и надежности CLI транспорта (`app/llm/cli_path_guard.py`)

## OAuth токены и сессии LLM
- Компонент `app/llm/session_manager.py` — `LLMSessionManager` управляет жизненным циклом LLM-адаптеров на сессию и роль, читает `configs/llm_routing.yaml`, выбирает провайдера и кэширует адаптеры.
- Фоновый демон автообновления токенов: `scripts/refresh_tokens_daemon.py` выполняет обновление access-токенов по refresh-токенам для всех провайдеров каждые 30 минут.
- `systemd`-сервис `oauth-refresh.service` запускает демон от пользователя `feature`, перезапускается всегда, пишет логи в `/var/log/oauth-refresh.log`.
- Первичная инициализация/авторизация провайдеров: `scripts/authorize_providers.py` сохраняет секреты в хранилище, без ручного вмешательства при последующих запусках.
- UI страницы для наблюдения: `/admin/agents` (OAuth статус агентов, версии CLI), `/admin/budget` (метрики расхода токенов с прогресс-барами).

## Orchestration: Backlog Loop
- Реализован цикл "самовыполнения" из бэклога
- Планировщик (`app/orchestrator/loop.py`) обрабатывает `features.NEW` и `tasks.NEW` каждые N секунд
- Автоматически вызывает Architect для генерации плана, если он отсутствует
- Запускает/резюмирует граф G1 для готовых задач
- Обрабатывает состояние `WAIT_BUDGET` для отложенных задач
- Поддерживает механизм повторных попыток при ошибках

## Orchestration: API
- Реализован REST API для интеграции с UI и скриптами:
  - `POST /api/v1/orchestrator/features` — создать фичу (Maintainer)
  - `POST /api/v1/orchestrator/features/{id}/plan` — Architect → DAG/DSL + package_contract → tasks
  - `POST /api/v1/orchestrator/features/{id}/run` — запустить/резюмировать G1
  - `GET /api/v1/orchestrator/graph/{run_id}/status` — статус узлов/чекпоинтов
- Все вызовы API логируются с `api_call_start/end`

## Gate & Policies
- Orchestrator валидирует artifact_manifest и package_contract в ответах агентов
- При отсутствующем или невалидном manifest → REJECT с событием `artifact_rejected`
- При отсутствующем package_contract в задачах Architect → REJECT
- При успешной валидации → APPLY с событиями `artifact_applied` и `doc_updated`
- Все события логируются и записываются в change_log

## Admin/UI и NL-flow
- Админка доступна по адресу `/admin` с BasicAuth
- SQLAdmin интерфейс: `/admin/sqladmin`
- Jobs view: таблица задач из `jobs`
- Logs tail: фильтрация логов из `agent_events`
- Docs status: статус документов из `doc_registry`
- Tokens stats: статистика использования токенов из `token_stats`
- NL форма: POST текст → вызов Maintainer (LLM) → показ intent/DAG (read-only)
- X-Request-ID в ответах для корреляции
