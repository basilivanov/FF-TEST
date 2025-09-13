# Selectors DSL

## Формат запроса

```json
{ "type": "code|docs|tests|logs", "filters": {...}, "top_k": 5, "since": "ISO8601|optional" }
```

### Типы и фильтры

* `code`: `symbol`, `module_path`, `calls_to/from`
* `docs`: `tags`, `path_contains`
* `tests`: `paths`, `marker`
* `logs`: `corr_id`, `level`, `since`

## Примеры

* Dev: `{ "type":"code", "filters":{"module_path":"app/index"}, "top_k":3 }`
* QA: `{ "type":"tests", "filters":{"paths":["tests/api"]}, "top_k":5 }`
* Scribe: `{ "type":"docs", "filters":{"tags":["Indexer"]}, "top_k":4 }`
* Architect: `{ "type":"code", "filters":{"calls_to":"app/api/orchestrator_v2.py"}, "top_k":5 }`

## Ограничения

* `top_k ≤ 8`, таймаут выборки 2s.