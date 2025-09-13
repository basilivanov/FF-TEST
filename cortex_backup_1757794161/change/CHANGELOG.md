# CHANGELOG

## v1.0.0 (MVP) — 2025-08-29

### Added
- OAuth Token Management finalized: centralized refresh tokens, background daemon `scripts/refresh_tokens_daemon.py`, and `systemd` service `oauth-refresh.service` for automatic access-token rotation.
- `LLMSessionManager` (`app/llm/session_manager.py`) to manage per-session, per-role LLM adapters based on `configs/llm_routing.yaml`.
- Mission Control Dashboard pages: `/admin/agents` (LLM agent status, OAuth indicators, CLI versions) and `/admin/budget` (token usage metrics with progress bars).
- Sudo-safe operational wrappers in `bin/` (`ff-ui-deploy-safe`, `ff-orch-*-safe`, `ff-netdiag-8081`, etc.) for controlled, repeatable ops flows.

### Changed
- Environment location-independence: agents, tests, and scripts now use `FF_API_BASE_URL` as the single source of truth for API base URL (with local default fallback).
- Docs updated to reflect final OAuth workflow and Dashboard: `docs/Architecture.md`, `docs/Security-Guide.md`, and `cortex/playbook/main.md`.

### Fixed
- Non-interactive OAuth stability for all LLM providers (Claude, Gemini, Codex, Qwen) via daemon-driven refresh; no manual re-auth required.


- Добавлена фича: Создан эндпоинт /api/v1/ping для feature #999 (QA: PASS)

- Добавлена фича: Создан эндпоинт /api/v1/ping для feature #1 (Smoke Test)


- Добавлена фича: Создан эндпоинт /api/v1/ping для feature #2 (Smoke Test)


## [2025-08-27]

### Added

- Implemented GET /api/v1/ping endpoint using `ping.py` script via Feature Factory process.

### Added
- Добавлены уставы ролей (Architect, Dev, QA, Scribe, Maintainer) в `agents/charters/`
- Добавлены системные промпты ролей в `agents/prompts/`
- Добавлены документы с политиками:
  - `docs/Context-Policy-000.md` - Политика контекста
  - `docs/Selectors-DSL-001.md` - Selectors DSL
  - `docs/Permissions-000.md` - Матрица прав
  - `docs/Schemas-Index.md` - Свод схем контрактов
  - `docs/ChangePolicy-Gate-001.md` - Gate Policy причины REJECT
  - `docs/LLM-Budgets-001.md` - Политика маршрутизации и бюджетов
- Добавлены QA-чек-листы для всех ролей в `docs/QA-Checklists/`
- Добавлены документы:
  - `runbook_E12_E2E_TEST_v2.md` - Runbook E2E (v2)
  - `docs/LangGraph-Nodes-Contracts.md` - Контракты узлов G1
  - `docs/API-Maintainer-001.md` - Maintainer Intake & Planning
  - `docs/UI-000.md` - Dashboard KPI
- Добавлены конфигурационные файлы:
  - `configs/prompts.yaml` - Карта промптов по ролям
  - `configs/llm_routing_v2.yaml` - Маршрутизация LLM v2 по ролям
- Добавлены новые документы:
  - `docs/Orch-Prompt-Load-Policy.md` - Политика загрузки промптов в узлах графа
  - `docs/Gate-Rules-Roles.md` - Правила Gate для ролей/промптов
  - `docs/Contracts-Package-Checklist.md` - Минимум для Architect/Dev/QA/Scribe ответов
  - `docs/Tokens-Policy-002.md` - Политика бюджетов по ролям v2
  - `docs/UI-Roles-Catalog.md` - Каталог ролей в UI
  - `runbook_RPS_UPDATE.md` - Runbook обновления уставов/промптов
- Добавлены документы для QA финал RPS:
  - `qa_signoff_RPS.md` - Итоговый QA отчет по RPS
  - `tests/gate_negative_matrix.md` - Таблица сценариев Gate Negative
  - `qa_report_gate_negative.md` - QA отчет по Gate Negative
- Добавлены документы для Orchestrator + Router защиты версий промптов:
  - `docs/Prompt-Versioning-001.md` - Правила пиннинга промптов по prompt_sha256 + rollback
  - `configs/prompts.lock.json` - Файл блокировки версий промптов
  - `docs/Router-Enforcement-001.md` - Политика enforce для Router
- Добавлены документы для Admin UI:
  - `ui_spec_roles_catalog.md` - Спецификация UI для каталога ролей
  - `docs/UI-Role-Metrics.md` - Метрики ролей в UI
- Добавлены документы для Maintainer Chat → Backlog (UAT сценарий):
  - `uat_script_maintainer_chat.md` - UAT сценарий для Maintainer Chat
  - `docs/Context-Scope-Policy.md` - Политика контекстного scope
- Добавлены документы для надёжности и устойчивости:
  - `qa_report_llm_chaos.md` - QA отчет по chaos testing LLM
  - `qa_report_budget_surge.md` - QA отчет по тестированию бюджетов
- Добавлены документы для CI блокировки и контроля изменений:
  - `docs/CI-RPS.md` - Документ по CI блокировкам RPS
  - `docs/Alerts-Prompt-Drift.md` - Документ по алертам дрейфа промптов
- Обновлен `docs/doc_registry.json` с новыми документами

### Changed
- Синхронизирована документация по маршрутизации LLM с llm_routing.yaml
- Обновлены существующие документы с описанием архитектуры и политик
