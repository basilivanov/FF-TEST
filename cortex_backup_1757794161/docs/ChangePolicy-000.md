# Change Policy (MVP)

## События системы

### Общие
- `job_scheduled` `job_started` `job_finished` `retry_scheduled` `rate_limited` `error`

### HTTP
- `api_call_start` `api_call_end`

### БД
- `db_upsert` `db_replace_batch` `db_migration_applied`

### LLM
- `llm_call_start` `llm_call_end` `llm_budget_exceeded` `llm_output_invalid`

### ETL
- `extract_page` `transform_batch` `load_batch` `watermark_advanced`

### Sheets
- `sheets_write_start` `sheets_write_end`

### Docs/Change
- `artifact_applied` `doc_updated` `changelog_written` `index_updated`
- `artifact_rejected`
- `missing_docs`

## Политики

### 1. `index_updated`
- **Инициатор:** Dev (скрипт индексации)
- **Условия:** При успешном обновлении реестра кода и индексов
- **Действия:** 
  - Логирование события в систему логов
  - Обновление времени последней индексации
- **Мониторинг:** QA отслеживает регулярность событий

### 2. `artifact_rejected`
- **Инициатор:** Orchestrator (gate)
- **Условия:** При отсутствии artifact_manifest в ответе агента или невалидном manifest
- **Действия:** 
  - Логирование события с причиной отклонения
  - Отказ от применения артефакта
- **Мониторинг:** QA отслеживает частоту отказов

### 3. `artifact_applied`
- **Инициатор:** Orchestrator (apply)
- **Условия:** При успешной валидации artifact_manifest и package_contract
- **Действия:** 
  - Применение артефакта
  - Запуск AutoIndex и DocSync
- **Мониторинг:** QA отслеживает успешность применения

### 4. `doc_updated`
- **Инициатор:** Orchestrator (DocSync)
- **Условия:** После успешного применения артефакта
- **Действия:** 
  - Обновление doc_registry
  - Логирование события обновления документации
- **Мониторинг:** QA отслеживает успешность обновления документации

### 5. `db_policy_violation`
- **Инициатор:** Orchestrator (gate)
- **Условия:** При нарушении политики работы с БД (см. _capsule.md#DB)
- **Действия:** 
  - Логирование события с причиной нарушения
  - Отказ от применения артефакта
- **Мониторинг:** QA отслеживает частоту отказов

### 6. `qa_policy_violation`
- **Инициатор:** Orchestrator (gate)
- **Условия:** При нарушении политики тестирования (см. _capsule.md#Tests)
- **Действия:** 
  - Логирование события с причиной нарушения
  - Отказ от применения артефакта
- **Мониторинг:** QA отслеживает частоту отказов

### 7. `missing_docs`
- **Инициатор:** Orchestrator (DocSync Guard)
- **Условия:** При применении артефакта, который изменил код, но не обновил соответствующую документацию
- **Действия:** 
  - Создание задачи для роли Scribe с указанием пропущенных документов
  - Логирование события с перечнем файлов, требующих документирования
- **Мониторинг:** QA отслеживает частоту пропущенных документов