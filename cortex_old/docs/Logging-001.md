# Logging-001: Единый стандарт логов (v1.2)
- **Цель:** одинаковые, парсируемые, информативные логи во всех модулях; дешёвые по объёму; без секретов.
- **Библиотеки:** structlog (JSON) + loguru (ротация). Все записи — только **JSON одной строки**.

## 1) Обязательные поля
- `ts`, `level`, `env`, `component`, `agent_role`, `run_id`, `task_id`, `correlation_id`, `event`, `kv{}`

## 2) Каталог событий
- Общие: `job_scheduled` `job_started` `job_finished` `retry_scheduled` `rate_limited` `error`
- HTTP: `api_call_start` `api_call_end`
- БД: `db_upsert` `db_replace_batch` `db_migration_applied`
- LLM: `llm_call_start` `llm_call_end` `llm_budget_exceeded` `llm_output_invalid`
- ETL: `extract_page` `transform_batch` `load_batch` `watermark_advanced`
- Sheets: `sheets_write_start` `sheets_write_end`
- Docs/Change: `artifact_applied` `doc_updated` `changelog_written`

## 3) Профили kv
- HTTP: `{method,url_host,url_path,status,duration_ms,attempt,retries,backoff_ms,req_bytes,resp_bytes}`
- БД: `{table,op,rows,conflicts,duration_ms}`
- LLM: `{provider,model,prompt_hash,input_tokens,output_tokens,latency_ms,cache_hit,budget_remaining}`
- ETL: `{source,page,items,total,window_from,window_to}`
- Sheets: `{spreadsheet_id,sheet,range,rows,cols,duration_ms}`

## 4) Уровни/сэмплинг
- INFO по умолчанию; DEBUG ≤5% (kv.sampling). ERROR: `err_type`,`err_msg` (без секретов), `stack:true`.

## 5) Маскирование
- Токены/секреты/PII → `***REDACTED***`. Payload не логируется.

## 6) Корреляция
- `correlation_id` на входе HTTP/джобы; `run_id` — на весь конвейер.

## 7) Helpers
- `@log_job`, `@log_http`, `@log_db`, `llm_log_context()` — обязательны для Dev.

## 8) Реализация
- Модуль: `app/logging_helpers.py`
- Middleware: `app/api/middleware.py`
- Декораторы автоматически логируют начало и завершение операций с правильными полями и kv-профилями.
