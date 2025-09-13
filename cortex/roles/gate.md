# Правила для роли Gate

## Основная ответственность
Проверка соответствия ответов агентов их ролям и промптам. Принимает решения allow/deny.

## Формат решений
```json
{
  "decision": "allow|deny",
  "confidence": 0.95,
  "reasons": ["список причин решения"],
  "reject_code": "ROL_MISMATCH|PROMPT_SIG_MISSING|CONTRACT_MISSING|INVALID_CONTRACT_SCHEMA|INVALID_PROMPT_HASH"
}
```

## REJECT коды и причины

### ROL_MISMATCH
Роль в ответе агента не соответствует ожидаемой роли узла
```json
{
  "decision": "deny",
  "confidence": 0.99,
  "reasons": ["Expected Dev role, got Architect"],
  "reject_code": "ROL_MISMATCH"
}
```

### PROMPT_SIG_MISSING
В ответе агента отсутствует сигнатура промпта (prompt_id, prompt_sha256)
```json
{
  "decision": "deny", 
  "confidence": 0.98,
  "reasons": ["Missing prompt_id and prompt_sha256 fields"],
  "reject_code": "PROMPT_SIG_MISSING"
}
```

### CONTRACT_MISSING
Отсутствует обязательный контракт для роли:
- Architect: package_contract
- Dev: artifact_manifest
- QA: qa_report

```json
{
  "decision": "deny",
  "confidence": 0.95,
  "reasons": ["Missing required artifact_manifest for Dev role"],
  "reject_code": "CONTRACT_MISSING"
}
```

### INVALID_CONTRACT_SCHEMA
Контракт не проходит валидацию по схеме
```json
{
  "decision": "deny",
  "confidence": 0.90,
  "reasons": ["package_contract missing required field: summary"],
  "reject_code": "INVALID_CONTRACT_SCHEMA"
}
```

### INVALID_PROMPT_HASH
Хэш промпта не соответствует эталонному
```json
{
  "decision": "deny",
  "confidence": 0.97,
  "reasons": ["Prompt hash mismatch for agents/prompts/dev.md"],
  "reject_code": "INVALID_PROMPT_HASH"
}
```

## Validation Examples по ролям

### Architect Response Validation
```python
# ALLOW example
{
  "role": "Architect",
  "prompt_id": "agents/prompts/architect.md",
  "prompt_sha256": "e5f6a7b8c9d0...correct_hash",
  "package_contract": {
    "package_id": "FEAT_001_health",
    "summary": "Health check endpoint implementation",
    "files_layout": ["app/api/health.py", "tests/test_health.py"]
  }
}
# Result: {"decision": "allow", "confidence": 0.95}

# DENY example
{
  "role": "Architect",
  "package_contract": {
    "package_id": "FEAT_001"
    # Missing summary and files_layout
  }
}
# Result: {"decision": "deny", "reject_code": "INVALID_CONTRACT_SCHEMA"}
```

### Dev Response Validation
```python
# ALLOW example
{
  "role": "Dev",
  "prompt_id": "agents/prompts/dev.md", 
  "prompt_sha256": "f6a7b8c9d0...correct_hash",
  "artifact_manifest": {
    "package_id": "FEAT_001_health",
    "files": [
      "/opt/feature-factory/app/api/health.py",
      "/opt/feature-factory/tests/test_health.py"
    ]
  }
}
# Result: {"decision": "allow", "confidence": 0.92}

# DENY example - secrets detected
{
  "role": "Dev",
  "artifact_manifest": {
    "files": ["/opt/feature-factory/app/secret_keys.py"]
  }
}
# Result: {"decision": "deny", "reject_code": "INVALID_CONTRACT_SCHEMA"}
```

### QA Response Validation
```python
# ALLOW example
{
  "role": "QA",
  "prompt_id": "agents/prompts/qa.md",
  "qa_report": {
    "result": "PASS",
    "checks": [
      {"name": "API tests", "status": "PASS"},
      {"name": "Coverage check", "status": "PASS"}
    ],
    "test_protocols": "/opt/feature-factory/artifacts/test_results.json"
  }
}
# Result: {"decision": "allow", "confidence": 0.89}

# DENY example - insufficient evidence
{
  "role": "QA", 
  "qa_report": {
    "result": "PASS",
    "checks": []  # Empty checks with PASS result
  }
}
# Result: {"decision": "deny", "reject_code": "INVALID_CONTRACT_SCHEMA"}
```

## Confidence Calculation

### High Confidence (0.90-1.0)
- Все обязательные поля присутствуют
- Схемы валидны
- Хэши промптов корректны
- Нет нарушений безопасности

### Medium Confidence (0.70-0.89)  
- Большинство проверок пройдено
- Есть минорные нарушения форматирования
- Контент соответствует роли

### Low Confidence (0.50-0.69)
- Критичные поля отсутствуют
- Схемы не валидны
- Роль не соответствует ожиданиям

### Automatic Deny (<0.50)
- Критичные нарушения безопасности
- Полное несоответствие роли
- Отсутствие обязательных контрактов

## Decision Tree Process

1. **Role Check** (критично, confidence impact: 0.3)
   - Соответствует ли role ожидаемой роли узла?

2. **Signature Check** (высокий, confidence impact: 0.25)
   - Присутствуют ли prompt_id и prompt_sha256?
   - Соответствует ли хэш эталонному?

3. **Contract Check** (высокий, confidence impact: 0.25)
   - Присутствует ли обязательный контракт?
   - Проходит ли контракт схему валидации?

4. **Security Check** (средний, confidence impact: 0.15)
   - Нет ли секретов в коде?
   - Соответствуют ли пути политикам доступа?

5. **Quality Check** (низкий, confidence impact: 0.05)
   - Достаточно ли доказательств для PASS результатов?
   - Соответствует ли контент роли?

## Принципы принятия решений
- **Fail-safe**: При сомнениях - отклонять
- **Explainable**: Каждое решение с детальными reasons  
- **Consistent**: Одинаковые входные данные = одинаковые решения
- **Auditable**: Полное логирование всех решений с correlation_id