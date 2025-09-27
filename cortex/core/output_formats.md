# Cortex Core — Output Formats (Unified)

Этот документ — единый источник форматов ответов ролей. Конкретные схемы находятся в `cortex/docs/*.schema.json`.

## Dev — Artifact Manifest (YAML)
- Должен быть ПЕРВЫМ блоком ответа.
- Требуемые поля: `package_id`, `files[].path` (+опц. `files[].content`, `dod[]`, `package_contract`).

## Architect — Package Contract + Tasks DSL
- `package_contract.yaml` (обязательные поля: `package_id`, `summary`, `files_layout[]`).
- `plan.dsl.yaml` (валидный DAG с ролями и зависимостями).

## QA — QA Report
- Итог `result: PASS|FAIL`, таблица `checks[]`, метрики.

## Scribe — DocSync
- Обновлённые документы (fenced markdown) + CHANGELOG delta + запись в `doc_registry` + событие `doc_updated`.

## Prompt Signature (для всех)
- `prompt_id`, `prompt_sha256` обязательны и логируются на каждом LLM‑вызове.

