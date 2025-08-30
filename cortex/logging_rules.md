# Logging Rules

- **Library:** Use `structlog` for JSON logging and `loguru` for rotation. All logs must be single-line JSON.
- **Required Fields:** `ts`, `level`, `env`, `component`, `agent_role`, `run_id`, `task_id`, `correlation_id`, `event`, `kv{}`.
- **Log Levels:** `INFO` by default. `DEBUG` should be sampled at <=5%.
- **Secrets:** All secrets, tokens, and PII must be redacted to `***REDACTED***`.
- **Helpers:** Use the provided logging helpers: `@log_job`, `@log_http`, `@log_db`, `llm_log_context()`.
- **Implementation:** The core logging logic is in `app/logging_helpers.py`.
