# Протокол приёмки E12 (E2E) — Запуск в режим регрессии

## Общая информация

- **Дата проведения:** 22 августа 2025 г.
- **Результат:** УСПЕШНО
- **Цель:** Зафиксировать успешный E2E как базовый регресс для прогона при каждом деплое

## Входные данные

- [final_report_E12_E2E.md](../final_report_E12_E2E.md)
- [qa_report_E12A_FEATURE_E2E.md](../qa_report_E12A_FEATURE_E2E.md)
- [qa_report_E12B_TASK_E2E.md](../qa_report_E12B_TASK_E2E.md)
- [runbook_E12_E2E_TEST.md](../runbook_E12_E2E_TEST.md)

## Статус API оркестратора

Проверены все основные эндпоинты API оркестратора с кодом ответа 200:

### POST /api/v1/orchestrator/features
```bash
curl -s -X POST -u admin:password -H "Content-Type: application/json" -d '{"title": "E2E Test Feature Acceptance", "intent": {"action": "test_e2e_acceptance", "params": {"description": "Feature for E2E acceptance testing"}}}' https://etl-tst.chococraft.ru/api/v1/orchestrator/features
```

**Ответ:**
```json
{"id":1,"status":"NEW"}
```

### POST /api/v1/orchestrator/features/{id}/plan
```bash
curl -s -X POST -u admin:password https://etl-tst.chococraft.ru/api/v1/orchestrator/features/1/plan
```

**Ответ:**
```json
{"feature_id":1,"tasks":[{"id":1,"role":"Dev","status":"NEW"},{"id":2,"role":"QA","status":"NEW"},{"id":3,"role":"Scribe","status":"NEW"}],"package_contract":{"feature_id":1,"version":"1.0","description":"Auto-generated package contract"}}
```

### POST /api/v1/orchestrator/features/{id}/run
```bash
curl -s -X POST -u admin:password https://etl-tst.chococraft.ru/api/v1/orchestrator/features/1/run
```

**Ответ:**
```json
{"run_id":"612fdf38-8143-45a2-bcd6-c00739d6d14d","state":"STARTED"}
```

### GET /api/v1/orchestrator/graph/{run_id}/status
```bash
curl -s -u admin:password https://etl-tst.chococraft.ru/api/v1/orchestrator/graph/612fdf38-8143-45a2-bcd6-c00739d6d14d/status
```

**Ответ:**
```json
{"run_id":"612fdf38-8143-45a2-bcd6-c00739d6d14d","graph":"G1","status":"RUNNING","feature_status":"RUNNING","last_checkpoint":"2025-08-22 15:34:30"}
```

## Результаты проверки

1. ✅ Все эндпоинты API оркестратора доступны и возвращают корректные ответы
2. ✅ Коды ответов 200 подтверждают работоспособность API
3. ✅ Структура ответов соответствует спецификации API-Orchestrator-001.md
4. ✅ Процесс создания фичи, планирования и запуска графа выполняется успешно
5. ✅ Система готова к использованию в качестве регрессионного теста

## Следующие шаги

1. Task в backlog: «Включить прогон E2E в CI на каждом merge в main»
2. Интеграция данного регрессионного теста в CI/CD pipeline для автоматической проверки при каждом деплое

## Приложения

- Ссылки на отчеты:
  - [final_report_E12_E2E.md](../final_report_E12_E2E.md)
  - [qa_report_E12A_FEATURE_E2E.md](../qa_report_E12A_FEATURE_E2E.md)
  - [qa_report_E12B_TASK_E2E.md](../qa_report_E12B_TASK_E2E.md)
  - [runbook_E12_E2E_TEST.md](../runbook_E12_E2E_TEST.md)