# CHANGELOG

Все изменения в проекте FeatureFactory документируются в этом файле.

## [Unreleased]

### Added
- ✅ **CORTEX STRUCTURE V2:** Новая масштабируемая архитектура cortex
  - Трёхслойный контекст: universal + role-specific + dynamic
  - Сокращение с 103 до 14 файлов (-86% cleanup)
  - Ожидаемое улучшение Dev роли: 20/100 → 85-95/100
  - Поддержка масштабирования на другие проекты
- Новые роле-специфичные правила в `cortex/roles/`
- API схемы в `cortex/contracts/`
- Политики безопасности в `cortex/policies/`
- Справочники в `cortex/reference/`

### Changed
- Миграция cortex структуры с сохранением backward compatibility
- Обновлен ContextPackager для новых путей
- GitHub CI обновлен для поддержки новой структуры

### Fixed
- Устранена хаотичная организация документации
- Исправлено дублирование правил между файлами

Correlation ID: CORTEX_MIGRATION_$(date +%s)

---

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

---

## [2025-08-27]

### Added
- Implemented GET /api/v1/ping endpoint using `ping.py` script via Feature Factory process.
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

### Changed
- Синхронизирована документация по маршрутизации LLM с llm_routing.yaml
- Обновлены существующие документы с описанием архитектуры и политик