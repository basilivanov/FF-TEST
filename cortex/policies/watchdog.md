# Watchdog Policy (TEST)

## Назначение
- Обнаружение повторяющихся ошибок инструментов и принятие решения об эскалации/ретрае без участия человека.
- Встраиваемый узел LangGraph между `dev` и `gate`.

## Источник политики
- Файл SSOT: `/opt/feature-factory/configs/watchdog_policy.yaml`
- Пример:
```
watchdog:
  enabled: true
  triggers:
    - type: consecutive_tool_failures
      tool_name: "any"
      error_type: "identical"
      threshold: 3
  escalation_protocol:
    - level: 1
      action: "retry_with_error_context"
    - level: 2
      action: "escalate_to_next_provider"
    - level: 3
      action: "fail_and_alert"
```

## Логика
- Узел `watchdog_check_node` (app/graph/nodes/watchdog.py):
  - Накапливает `watchdog_failures` на основе `tool_errors` из состояния графа
  - При достижении `threshold` для одинаковых `tool_name`/`error_type` → решение `ESCALATE_L1`
  - Формирует `escalation_context` (сводка ошибок), возвращает `watchdog_decision`
- Граф G1 (app/graph/g1_feature.py):
  - Ребро: `dev → watchdog_check → (dev|gate)` по функции `decide_after_watchdog`

## События/Наблюдаемость
- Логи:
  - `watchdog_triggered` (warning) — содержит `threshold` и список последних ошибок
  - `task_escalated` (info) — уровень и действие (`retry_with_error_context`)
  - `dev_node_retry_with_context` — повтор узла Dev с добавленным контекстом
- Метрики: учитываются в общих `runner_*`; доп. алерты на всплески `watchdog_triggered`

## UI‑интеграция
- Dashboard → «Центр инцидентов» группирует события Watchdog с CTA «Перезапустить Dev / Эскалировать»
- Feature Detail → бейдж решения Watchdog на переходе `dev → gate`, панель с `escalation_context`
- SSE: события Watchdog поступают через логи; при необходимости расширить стрим доменными событиями

## DoD
- При 3 последовательных одинаковых сбоях инструментов граф не падает, а выполняет L1‑эскалацию и завершает сценарий
- События логируются, UI их отображает; политика переключаема из SSOT‑файла

