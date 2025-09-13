# Контракты узлов G1

## Общие

Стейты: NEW→RUNNING→DONE / RETRYABLE_ERROR / FAILED / WAIT_BUDGET.
События: `job_started`, `job_finished`, `artifact_generated`, `artifact_applied`, `doc_updated`.

### Dev

**Вход:** `task_id`, `package_contract`.
**Выход:** `artifact_manifest` + файлы (`tmp/{run_id}/`).
**Метрики:** длительность p50/p95, размер артефактов, ретраи%.
**Идемпотентность:** повтор — перезапишет `tmp/{run_id}/`.

### Gate

**Вход:** манифест/контракт.
**Выход:** `artifact_applied` или REJECT.
**Метрики:** % REJECT по кодам.

### QA

**Вход:** артефакты/схемы.
**Выход:** `qa_report` PASS/FAIL.
**Метрики:** PASS rate, крит.ветки покрытие.

### Scribe

**Вход:** артефакты/qa_report.
**Выход:** обновлённые `docs/*`, `CHANGELOG`, `doc_registry`.
**Метрики:** время синхронизации, битые ссылки%.

### Apply

**Вход:** валидные артефакты.
**Выход:** применение, триггер AutoIndex/DocSync.
**Метрики:** длительность, успешность.

*(Можно добавить Mermaid-диаграмму, но текст достаточно.)*