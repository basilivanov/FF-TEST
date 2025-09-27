# Cortex → Admin UI: контракты и UX (TEST)

## Карта экранов
- Mission Control Dashboard
  - Инциденты (агрегация логов + `watchdog_*`)
  - Индекс/Документация (актуальность, `docs/rebuild`)
  - Статусы агентов LLM

- Feature Detail ("Карта полёта")
  - DAG узлов: `dev → watchdog → gate → qa → scribe → apply`
  - Правая панель узла: ошибки инструмента, решение Watchdog, контекст эскалации
  - Хронолента событий: `job_*`, `task_escalated`, `watchdog_triggered`

- Cortex Раздел
  - Docs: `GET /api/v1/docs/status`, `POST /api/v1/docs/rebuild`
  - Index: поиск символов/модулей, карточки модулей
  - CallGraph: `GET /api/v1/index/calls` (фильтры source/target/file)

## API‑контракты (использование UI)
- Docs
  - `GET /api/v1/docs/status` → список документов (doc_registry)
  - `POST /api/v1/docs/rebuild` → пересчёт хэшей, обновление `updated_at`

- Index
  - `GET /api/v1/index/symbol?symbol_name=&file_path=` → поиск в `symbol_index`
  - `GET /api/v1/index/module-card?file_path=` → карточка модуля
  - `GET /api/v1/index/calls?...` → ребра `call_graph_edges`

- SSE
  - `GET /api/v1/stream/events` → типы событий: `connection_opened|job_started|job_finished|error|index_updated|doc_updated|connection_closed`
  - UI‑агрегатор: троттлинг до 4–6 ререндеров/с, backoff переподключения 1s→5s

## Маппинг данных → UX
- Watchdog
  - Источник: логи (`watchdog_triggered`, `task_escalated`, `dev_node_retry_with_context`)
  - Отображение: бейджи/метки на узлах графа; карточка решения (`CONTINUE|ESCALATE_L1`), список последних ошибок инструмента
  - Действия: «Перезапуск узла Dev», «Эскалировать провайдера», «Открыть контекст ошибок»

- Docs / Index
  - В дашборде: виджеты «Docs актуальны» и «Индекс активен» (по `docs/status` и `index_updated`)
  - В разделе Cortex: таблица реестра docs, поиск, карточки модулей; CallGraph с подсветкой по фильтрам

## Гардрейлы
- Только `/api/v1/*` и `/.well-known/ff-context.json`
- Без прямых вызовов `/orchestrator/*` (старые пути — удалить/перемапить)
- Graceful degradation: при 5xx/timeout — скелетон + подсказка, без падений UI

## DoD для внедрения
- Обновлённые страницы Dashboard/FeatureDetail/Docs/CallGraph читают реальные `/api/v1/*`
- SSE подключён и не деградирует производительность (без утечек)
- Для отсутствующих бэкенд‑эндпоинтов — заметные заглушки («данные недоступны»)

