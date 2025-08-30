# HL-2 (WRITE) — Выровнять адаптеры запуска CLI под строгий JSON

## Отчет о выполнении

**Цель:** Чтобы Maintainer/Architect/QA/Scribe реально выполнялись первым доступным провайдером по цепочке и возвращали строгий JSON.

**Выполненные изменения:**

1.  **Общие изменения:**
    *   Удалено добавление флага `-y` из команд `run` для всех провайдеров (оставлено только для `login` в `cli_path_guard.py`, где это было необходимо).
    *   Обеспечена передача сообщений в формате `messages_json` через `stdin` для всех провайдеров.
    *   Реализован `output_parser: json` с `text+json_extract` fallback для всех провайдеров. Это означает, что адаптеры сначала пытаются распарсить вывод CLI как чистый JSON, а в случае неудачи пытаются извлечь JSON-подобную структуру из текстового вывода.
    *   Добавлено логирование `llm_call_start` и `llm_call_end` в `app/llm/transports/cli.py`, включающее полную команду, код возврата и `stderr` (без токенов).

2.  **Изменения по провайдерам:**
    *   **claude (Opus 4.1) (`app/llm/providers/claude.py`):**
        *   Добавлены флаги `--quiet` и `--json` для обеспечения строгого JSON-вывода.
        *   Изменена логика `build_cmd` для передачи сообщений через `stdin` в JSON-формате.
        *   Обновлен `parse_stdout` для поддержки `text+json_extract`.
    *   **openai (via codex GPT-5) (`app/llm/providers/gpt.py`):**
        *   Добавлен флаг `--quiet`.
        *   Изменена логика `build_cmd` для передачи сообщений через `stdin` в JSON-формате и удален аргумент `--input`.
        *   Обновлен `parse_stdout` для поддержки `text+json_extract`.
    *   **gemini 2.5 (`app/llm/providers/gemini.py`):**
        *   Удален флаг `-y`.
        *   Добавлен флаг `--response-mime-type application/json`.
        *   Изменена логика `build_cmd` для передачи сообщений через `stdin` в JSON-формате.
        *   Обновлен `parse_stdout` для поддержки `text+json_extract`.
    *   **qwen (`app/llm/providers/qwen.py`):**
        *   Удален флаг `-y`.
        *   Изменена логика `build_cmd` для передачи сообщений через `stdin` в JSON-формате.
        *   Обновлен `parse_stdout` для поддержки `text+json_extract`.

**Deliverables:**

*   `reports/LLM-ADAPTERS-R4/apply_log.md` (данный файл)
