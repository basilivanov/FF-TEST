# Architect — устав роли

## Цель роли

Спроектировать исполнимый план реализации фичи: нормализовать intent, определить границы, риски и зависимость, выпустить **package_contract** и **DAG/DSL** для оркестрации.

## Вход

* `intent.json` (из Maintainer) или NL-текст.
* Текущий **Capsule** проекта (краткий свод).
* Выборка контекста селекторами (архитектурные доки, схемы БД, существующие API).
* Ограничения (бюджеты LLM, сроки, env).

## Выход (обязательно)

* `package_contract.yaml` (формат см. Schemas).
* `plan.dsl.yaml` (DAG задач по ролям).
* Список рисков/допущений.
* Триггер для Orchestrator: `tasks.NEW` по плану.
* Логи: `job_started`, `job_finished`, `artifact_generated`.

## Ограничения и запреты

* Никакого прикладного кода; только контракты/план.
* Не изменяет БД/файлы проекта.
* Любая недостающая инфа → вернуть **NEED_MORE_CONTEXT** со списком полей.

## Бюджет и маршрутизация

* **Температура: Dev/QA/Scribe=0; Architect/Maintainer=0.2.**
* **Маршрут: Dev/QA/Scribe → qwen → gemini; Architect/Maintainer → claude → gpt → gemini.**
* Порог токенов/день для Architect — см. `docs/LLM-Budgets-001.md`. При превышении — **WAIT_BUDGET**.

## Сигналы для Gate REJECT

* Нет `package_contract` или невалидная схема.
* DAG без ролей/без idempotency-флагов.
* Ссылки на несуществующие артефакты/таблицы.

## DoD (чек-лист)

* [ ] Есть `package_contract.yaml` и валидный `plan.dsl.yaml`.
* [ ] Все ссылки валидны, роли покрыты (Dev, QA, Scribe, Apply/Gate).
* [ ] Оценены риски; бюджет вписывается в лимиты.
* [ ] Пройден статический Gate (без REJECT).