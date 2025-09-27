# Ops-Watchdog-SelfHealing (TEST)

## Purpose
- Непрерывный авто‑контур самоисцеления пайплайна фич без участия человека: создание фич → ускорение раннера → диагностика → переигровка до DoD.
- Снимает «системные» блокеры у агентов (API/валидации/маршрутизация/хуки), не вмешиваясь в прикладной код фич.

## Invariants
- only_wrappers_nosudo_for_services: рестарты/запуски только через bin/обёртки.
- no_mocks_in_prod (в TEST DRY_RUN=false), corr_id_required: каждый вызов с `X-Correlation-Id`.
- Секреты не логируются: используются ссылки `<SECRET:KEY>`; значения — из secret_store/ENV.
- Идемпотентность: повторы безопасны (ключи `{title, env}` + `corr_id`).
- Наблюдаемость: SSE/логи/метрики, экспоненциальный backoff, артефакты в FS.
- Агенты пишут фичу; watchdog правит только фабрику/конвейер (и системные промпты при отклонениях контрактов).

## Components
- `bin/ff-watchdog-loop-nosudo` — основной цикл (seed → heal → replay → tick).
- `bin/ff-watchdog-start-nosudo|stop|status` — запуск/останов/статус фоновых процессов.
- Обёртки сервисов: `ff-orch-restart-safe`, `ff-runner-{start,stop,status,restart}-nosudo`.
- Артефакты: `/opt/feature-factory/artifacts/watchdog/` → `watchdog.log`, `dlq.jsonl`, `ticker.log`, `sse.log`, `*.pid`.

## Control Loops
- Seeder: создаёт фичи по fallback‑цепочке
  - A_template (intent.template=notifications/telegram + slots с `<SECRET:…>`)
  - B_handoff (строгий YAML‑handoff по SSoT)
  - C_minimal (минимальный intent)
- Remediator (HEAL): классификация сбоев (422/5xx/AttributeError/429) по SSE/логам → создание HEAL‑фич (Architect→Dev→QA→Scribe→Apply) → ожидание merge → replay.
- Replay/DLQ: хранит неудачные попытки, переигрывает с backoff и respect Retry‑After.
- Runner Accelerator: тикает `POST /api/v1/runner/run-once` каждые 3s.
- Gatekeeper: проверяет DRY_RUN=false, секреты, LLM routing; при нарушении — DLQ с причиной.

## Failure Patterns → HEAL
- Create API рассинхрон (пример): `FeatureCreateRequest` vs SQL schema.
  - Fix (fabric): динамический разбор колонок `features` (PRAGMA), совместимые INSERT‑ы, дефолт `type='BUSINESS'` под CHECK‑constraint.
  - Применение: `ff-orch-restart-safe`.
- Secrets/ENV отсутствуют → HEAL‑SECRETS‑PRESENT: диагностика через debug‑эндпоинты, маскирование токенов.
- LLM routing/timeouts → HEAL‑LLM‑ROUTING: включить провайдеры, таймауты, фолбэки.
- GitHub auth → HEAL‑GITHUB‑AUTH: App→PAT fallback, логирование метода.

## Ops (Runbook)
- Старт фоновых процессов: `/opt/feature-factory/bin/ff-watchdog-start-nosudo`
- Статус: `/opt/feature-factory/bin/ff-watchdog-status-nosudo`
- Рестарт API: `/opt/feature-factory/bin/ff-orch-restart-safe`
- Рестарт runner: `/opt/feature-factory/bin/ff-runner-restart-nosudo`
- Логи: `tail -f /opt/feature-factory/artifacts/watchdog/watchdog.log`

## Telemetry & DoD
- Ожидаемые события: `feature_status_changed` (NEW→PLANNED→RUNNING→DONE|FAILED), `telegram_send_attempt/end`.
- Метрики: runner_*, db_rw_ok, ui_bundle_hash; без утечек секретов.
- DoD (TG‑фича): авто‑создание, статусы проходят, реальные Telegram‑сообщения приходят, DLQ пуст.

## Security
- Секреты — только ключи/маски; значения не попадают в логи/артефакты.
- Внешние вызовы — с проверкой статусов и ретраями; respect Retry‑After (429).

## Notes
- Watchdog — операционный контур; он не заменяет агентов и не «пишет фичи». Его задача — гарантировать, что конвейер агентов может пройти от фичи до merge.

