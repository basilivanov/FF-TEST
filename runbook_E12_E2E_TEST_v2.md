# Runbook E2E (v2)

## Сценарий A — Feature

1. POST /features → id
2. POST /plan
3. POST /run (resume-идемпотентный)
4. Poll /graph/{run_id}/status → DONE
5. Проверка артефактов + событий (index_updated, doc_updated)
   **Критерии**: ноль 5xx, DONE, логи LLM, индексы/реестры обновлены.

## Сценарий B — Task

1. Создать feature+plan → взять Dev task_id
2. Запуск G1 по task_id
3. Узлы Dev→Gate→QA→Scribe→Apply = DONE
   **Критерии**: DONE, валидные логи, манифест/доки на месте.

## Типичные сбои и что делать

* `WAIT_BUDGET` → дождаться лупа; срочно — дубль с override.
* `REJECT_*` → смотреть Gate-код, править причину.