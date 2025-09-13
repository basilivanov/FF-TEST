# Commands-NL: Натуральный язык → интенты → действия

## Схема `intent`
```json
{
  "intent": "plan_feature|run_import_ozon|run_normalize|run_export_sheets|set_schedule|status_jobs|logs_tail|docs_status|docs_rebuild|dry_run_toggle",
  "env": "test|prod",
  "slots": { "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "sheet": "Имя", "range": "A1", "time": "HH:MM", "days": "mon-fri", "component": "job|db|llm|*", "level": "INFO|ERROR", "last": 200, "on": true }
}
```

## Примеры → intent
- «Импортируй Озон за вчера в тесте» → `{intent:"run_import_ozon", env:"test", slots:{from:"yesterday", to:"yesterday"}}`
- «Сделай отчёт в гугл шитс Продажи‑день на A1» → `{intent:"run_export_sheets", slots:{sheet:"Продажи-день", range:"A1"}}`
- «Поставь импорт по будням на 09:15» → `{intent:"set_schedule", slots:{time:"09:15", days:"mon-fri"}}`
- «Покажи последние 100 ошибок БД» → `{intent:"logs_tail", slots:{component:"db", level:"ERROR", last:100}}`
- «Покажи статус задач» → `{intent:"status_jobs", env:"test"}`
- «Покажи документы» → `{intent:"docs_status", env:"test"}`

## Админские команды через NL
- «Покажи последние задачи» → `{intent:"status_jobs", env:"test"}`
- «Покажи последние 50 логов» → `{intent:"logs_tail", slots:{last:50}}`
- «Покажи статус документов» → `{intent:"docs_status", env:"test"}`

## Потоки
1) User → Maintainer (NL)
2) Maintainer → (а) Architect с задачами DSL **или** (б) Orchestrator с machine‑intent, если всё ясно.
3) Orchestrator исполняет/планирует, Scribe обновляет документы (DocSync).
