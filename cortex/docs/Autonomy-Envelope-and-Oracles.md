# Autonomy Envelope & Oracles (MVP)

Цель: повысить долю полностью автоматических успешных прогонов за счёт формализации оракулов (приёмочные тесты, инварианты) и расширения графа выполнения.

## Новые узлы графа

- SpecSynth — синтез спецификации/оракулов на базе intent (архитектурный DSL):
  - Формирует `architect_spec.json` в каталоге артефактов ран-а
  - Поля: `acceptance_tests.api`, `invariants`, `feature_flags`, `migrations`, `perf_budget`, `security_policies`, `budgets`, `dod`
- TestSynth — генерирует приемочные тесты (`test_acceptance_oracles.py`):
  - Базовые оракулы: `/openapi.json`, `/health/live`
  - Динамические проверки сгенерированных роутеров (без параметров пути) из `artifact_manifest.yaml`
  - Спек‑ориентированные API‑тесты по `architect_spec.json` (method/path/expected_status + опц. JSON‑schema)
  - Миграционные проверки Alembic (upgrade head → downgrade base) при наличии секции `migrations` в спецификации

## Обновление графа G1

Поток: `SpecSynth → TestSynth → Dev → Watchdog → Gate → QA → Scribe → Apply`

- Entry point перенесён на `SpecSynth`
- QA теперь собирает и запускает все тесты в каталоге артефактов, включая приёмочные оракулы
- PYTHONPATH в QA расширен: сначала артефакты, затем корень проекта `/opt/feature-factory`

## Схемы/контракты

Расширена схема `configs/schemas/architect.plan.schema.json` (концепт) новыми полями: `acceptance_tests`, `feature_flags`, `migrations`, `perf_budget`, `security_policies`. На практике узел SpecSynth создаёт файл `architect_spec.json` в этом формате.

## Ограничения и дальнейшие шаги

- SpecSynth использует intent из БД (`features.intent_json`) и формирует минимально полезные оракулы. Можно усилить через LLM и доменный DSL.
- TestSynth покрывает только роуты без параметров и базовые health/openapi проверки. Следующий шаг — генерация тестов по DSL (метод/путь/схема ответа).
- Gate оставлен прежним (валидация манифеста/путей/секретов). Жёсткая блокировка по тестам — на этапе QA (должно быть `PASS`).

## Ожидаемый эффект

- Для фич внутри «оболочки автономии»: рост auto‑PASS до 80–95% за счёт ранних оракулов и автогенерации тестов.
- Быстрый фидбек: любые проблемы проявляются до Apply, откаты не требуются.

## Watchdog интеграция после QA

- При провале QA (qa_result != PASS) состояние содержит tool_errors и escalation_context с кратким отчётом о провале.
- Граф маршрутизирует `QA → Watchdog` с автоматическим возвратом на Dev (ESCALATE_L1) при необходимости.
- Dev встраивает escalation_context в prompt и регенерирует артефакты.
