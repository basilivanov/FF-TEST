# Таблица сценариев Gate Negative

## Обзор

В этом документе описаны сценарии негативного тестирования Gate, которые проверяют корректность обработки различных ошибок и отклонений в ответах агентов.

## Сценарии тестирования

| ID | Название | Описание | Ожидаемый результат | Reject Code |
|----|----------|----------|-------------------|-------------|
| NEG-001 | ROL_MISMATCH | Отправка ответа с некорректной ролью | Отклонение ответа | ROL_MISMATCH |
| NEG-002 | PROMPT_SIG_MISSING | Отправка ответа без сигнатуры промпта | Отклонение ответа | PROMPT_SIG_MISSING |
| NEG-003 | CONTRACT_MISSING | Отправка ответа без обязательного контракта | Отклонение ответа | CONTRACT_MISSING |
| NEG-004 | BUDGET_MISSING | Отправка ответа без информации о бюджете | Отклонение ответа | BUDGET_MISSING |
| NEG-005 | MANIFEST_MALFORMED | Отправка ответа с некорректным форматом манифеста | Отклонение ответа | INVALID_CONTRACT_SCHEMA |
| NEG-006 | NO_FILES | Отправка ответа без файлов (для Dev) | Отклонение ответа | CONTRACT_MISSING |
| NEG-007 | INVALID_PROMPT_HASH | Отправка ответа с некорректным хэшем промпта | Отклонение ответа | INVALID_PROMPT_HASH |
| NEG-008 | MISSING_REQUIRED_FIELDS | Отправка ответа с отсутствующими обязательными полями | Отклонение ответа | INVALID_CONTRACT_SCHEMA |

## Детали сценариев

### NEG-001: ROL_MISMATCH
- **Описание**: Отправка ответа от узла Dev с указанием роли Architect
- **Проверяемый функционал**: Проверка соответствия роли в ответе и ожидаемой роли узла
- **Reject Code**: ROL_MISMATCH
- **Логирование**: 
  ```
  {
    "event": "artifact_rejected",
    "reason": "ROL_MISMATCH",
    "expected_role": "Dev",
    "actual_role": "Architect",
    "task_id": "task_12345"
  }
  ```

### NEG-002: PROMPT_SIG_MISSING
- **Описание**: Отправка ответа без обязательных полей prompt_id и prompt_sha256
- **Проверяемый функционал**: Проверка наличия сигнатуры промпта в ответе
- **Reject Code**: PROMPT_SIG_MISSING
- **Логирование**: 
  ```
  {
    "event": "artifact_rejected",
    "reason": "PROMPT_SIG_MISSING",
    "missing_fields": ["prompt_id", "prompt_sha256"],
    "task_id": "task_12345"
  }
  ```

### NEG-003: CONTRACT_MISSING
- **Описание**: Отправка ответа Architect без package_contract
- **Проверяемый функционал**: Проверка наличия обязательного контракта
- **Reject Code**: CONTRACT_MISSING
- **Логирование**: 
  ```
  {
    "event": "artifact_rejected",
    "reason": "CONTRACT_MISSING",
    "missing_contract": "package_contract",
    "role": "Architect",
    "task_id": "task_12345"
  }
  ```

### NEG-004: BUDGET_MISSING
- **Описание**: Отправка ответа без информации о бюджете (для Architect)
- **Проверяемый функционал**: Проверка наличия информации о бюджете в контракте
- **Reject Code**: BUDGET_MISSING
- **Логирование**: 
  ```
  {
    "event": "artifact_rejected",
    "reason": "BUDGET_MISSING",
    "missing_field": "budget",
    "role": "Architect",
    "task_id": "task_12345"
  }
  ```

### NEG-005: MANIFEST_MALFORMED
- **Описание**: Отправка ответа Dev с некорректным форматом artifact_manifest
- **Проверяемый функционал**: Проверка валидности схемы манифеста
- **Reject Code**: INVALID_CONTRACT_SCHEMA
- **Логирование**: 
  ```
  {
    "event": "artifact_rejected",
    "reason": "INVALID_CONTRACT_SCHEMA",
    "contract_type": "artifact_manifest",
    "validation_errors": ["invalid type for field 'files'"],
    "role": "Dev",
    "task_id": "task_12345"
  }
  ```

### NEG-006: NO_FILES
- **Описание**: Отправка ответа Dev с пустым списком файлов
- **Проверяемый функционал**: Проверка наличия файлов в артефакте
- **Reject Code**: CONTRACT_MISSING
- **Логирование**: 
  ```
  {
    "event": "artifact_rejected",
    "reason": "CONTRACT_MISSING",
    "missing_contract": "files",
    "role": "Dev",
    "task_id": "task_12345"
  }
  ```

### NEG-007: INVALID_PROMPT_HASH
- **Описание**: Отправка ответа с некорректным хэшем промпта
- **Проверяемый функционал**: Проверка соответствия хэша промпта эталонному значению
- **Reject Code**: INVALID_PROMPT_HASH
- **Логирование**: 
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

### NEG-008: MISSING_REQUIRED_FIELDS
- **Описание**: Отправка ответа Architect без обязательного поля summary в package_contract
- **Проверяемый функционал**: Проверка наличия обязательных полей в контракте
- **Reject Code**: INVALID_CONTRACT_SCHEMA
- **Логирование**: 
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