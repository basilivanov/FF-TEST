# Правила Gate для ролей/промптов

## Общие положения

Gate проверяет соответствие ответов агентов их ролям и промптам. При несоответствии Gate отклоняет ответы с соответствующими кодами.

## REJECT-коды

### ROL_MISMATCH
- **Причина**: Роль в ответе агента не соответствует ожидаемой роли узла
- **Пример лог-события**:
  ```
  {
    "event": "artifact_rejected",
    "reason": "ROL_MISMATCH",
    "expected_role": "Dev",
    "actual_role": "Architect",
    "task_id": "task_12345"
  }
  ```

### PROMPT_SIG_MISSING
- **Причина**: В ответе агента отсутствует сигнатура промпта (prompt_id, prompt_sha256)
- **Пример лог-события**:
  ```
  {
    "event": "artifact_rejected",
    "reason": "PROMPT_SIG_MISSING",
    "missing_fields": ["prompt_id", "prompt_sha256"],
    "task_id": "task_12345"
  }
  ```

### CONTRACT_MISSING
- **Причина**: В ответе агента отсутствует обязательный контракт (package_contract для Architect, artifact_manifest для Dev)
- **Пример лог-события**:
  ```
  {
    "event": "artifact_rejected",
    "reason": "CONTRACT_MISSING",
    "missing_contract": "package_contract",
    "role": "Architect",
    "task_id": "task_12345"
  }
  ```

### INVALID_CONTRACT_SCHEMA
- **Причина**: Контракт в ответе агента не проходит валидацию по схеме
- **Пример лог-события**:
  ```
  {
    "event": "artifact_rejected",
    "reason": "INVALID_CONTRACT_SCHEMA",
    "contract_type": "package_contract",
    "validation_errors": ["missing required field 'summary'"],
    "role": "Architect",
    "task_id": "task_12345"
  }
  ```

### INVALID_PROMPT_HASH
- **Причина**: Хэш промпта в ответе агента не соответствует эталонному хэшу
- **Пример лог-события**:
  ```
  {
    "event": "artifact_rejected",
    "reason": "INVALID_PROMPT_HASH",
    "expected_hash": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
    "actual_hash": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
    "prompt_id": "agents/prompts/dev.md",
    "role": "Dev",
    "task_id": "task_12345"
  }
  ```

## Обязательные поля для ответов по ролям

### Architect
- `package_contract.yaml` с обязательными полями:
  - `package_id`
  - `summary`
  - `files_layout`
- Сигнатура промпта:
  - `prompt_id`
  - `prompt_sha256`

### Dev
- `artifact_manifest.yaml` с обязательными полями:
  - `package_id`
  - `files`
- Сигнатура промпта:
  - `prompt_id`
  - `prompt_sha256`

### QA
- `qa_report.md` или `qa_report.json` с обязательными полями:
  - `result` (PASS/FAIL)
  - `checks`
- Сигнатура промпта:
  - `prompt_id`
  - `prompt_sha256`

### Scribe
- Обновленные документы в `docs/*`
- Событие `doc_updated` в логах
- Сигнатура промпта:
  - `prompt_id`
  - `prompt_sha256`

### Maintainer
- `intent.json` с обязательными полями:
  - `title`
  - `class`
  - `scope`
- Сигнатура промпта:
  - `prompt_id`
  - `prompt_sha256`