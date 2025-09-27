# Index & Docs — контракты для UI (TEST)

## Docs Registry API
- `GET /api/v1/docs/status`
  - Ответ: `{ docs: [{ doc_name, version, content_hash, updated_at }] }`
  - Источник: таблица `doc_registry` (SQLite)

- `POST /api/v1/docs/rebuild`
  - Ответ: `{ status: 'success'|'error', message, docs_updated }`
  - Поведение: пересчитать `content_hash` файлов, обновить `updated_at`

## Index API
- `GET /api/v1/index/symbol?symbol_name=&file_path=` → `{ symbols: [...] }`
  - Фильтры: по имени символа и/или пути файла
  - Назначение: быстрый поиск в `symbol_index`

- `GET /api/v1/index/module-card?file_path=` → `{ module_card: {...} }`
  - Назначение: карточка модуля (ключевые экспортированные элементы, краткая сводка)

- `GET /api/v1/index/calls?limit&offset&source_symbol&target_symbol&file_path`
  - Ответ: `{ edges:[{id,source_symbol,target_symbol,file_path,line_number}], total, limit, offset, as_of, stale }`
  - Назначение: построение CallGraph (React Flow/Nivo), фильтры по символам/файлу

## SSE события (`GET /api/v1/stream/events`)
- Типы: `connection_opened`, `job_started`, `job_finished`, `error`, `index_updated`, `doc_updated`, `connection_closed`
- Рекомендации для UI:
  - Троттлинг рендеров и батчинг обновлений
  - Авто‑переподключение с backoff (+ health‑индикатор в шапке)

## Анти‑кейсы и деградация
- Нет таблиц индекса → `stale=true` и пустые наборы (defensive в API). UI показывает пустые состояния/подсказки.
- Ошибки 5xx → не ронять страницу; показать `Retry` и ссылку на логи.

## DoD для UI
- Таблица docs заполняется из `/api/v1/docs/status`; `rebuild` меняет `updated_at`
- CallGraph грузит ребра страницами, фильтры работают; подсветка stale
- Поиск символов и карточки модулей открываются без ошибок

