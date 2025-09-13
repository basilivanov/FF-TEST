# Role Prompt Specifications

## XML Envelope Standard

All roles use unified XML envelope format:

```xml
<prompt>
<role>{ROLE_NAME}</role>
<context>
<system_knowledge>{STATIC_KNOWLEDGE}</system_knowledge>
<user_intent>{USER_REQUEST}</user_intent>
<previous_steps>{PIPELINE_STATE}</previous_steps>
</context>
<task>{SPECIFIC_TASK}</task>
<rules>
<positive>{ALLOWED_BEHAVIORS}</positive>
<negative>{FORBIDDEN_BEHAVIORS}</negative>
</rules>
<output_format type="{FORMAT_TYPE}">{SCHEMA_REFERENCE}</output_format>
<code>{IMPLEMENTATION_DIRECTIVE}</code>
</prompt>
```

## Role-Specific Output Formats

### Architect
- **Type**: `json_object`
- **Schema**: `plan_dsl per Architect schema`
- **Example**:
```json
{
  "plan_type": "endpoint",
  "components": ["health_check"],
  "estimated_effort": "low",
  "touchpoints": ["app/api/health.py"],
  "constraints": ["no_secrets", "readonly_ops"]
}
```

### Dev
- **Type**: `text`
- **Schema**: `code with unique markers`
- **Example**:
```python
# DEV_MARKER_{{corr_id}}
def health_endpoint():
    return {"status": "ok", "timestamp": datetime.utcnow()}
```

### QA
- **Type**: `json_object`
- **Schema**: `qa_report per QA schema`
- **Example**:
```json
{
  "validation_status": "pass",
  "issues": [],
  "test_coverage": 85,
  "recommendations": ["Add error handling"]
}
```

### Gate
- **Type**: `json_object`
- **Schema**: `allow/deny decision with reasons`
- **Example**:
```json
{
  "decision": "allow",
  "confidence": 0.9,
  "reasons": ["low_risk", "standard_endpoint", "no_secrets"],
  "conditions": []
}
```

### Scribe
- **Type**: `json_object`
- **Schema**: `changelog per Scribe schema`
- **Example**:
```json
{
  "changelog_entry": "Added health check endpoint",
  "version": "1.0.1",
  "category": "feature",
  "impact": "low"
}
```

### Apply
- **Type**: `json_object`
- **Schema**: `git operations status`
- **Example**:
```json
{
  "git_status": "ready",
  "files_changed": 1,
  "branch": "feature/health_check",
  "commit_sha": null,
  "pr_url": null
}
```

## Common Rules

### Positive Rules (All Roles)
- Строго соблюдать XML envelope format
- Возвращать только JSON согласно output_format (кроме Dev)
- Работать как роль со специализированными обязанностями
- Использовать корреляционные ID для трассировки

### Negative Rules (All Roles)
- Не читать/писать секреты в артефакты
- Не изменять код вне разрешенных путей
- Не отключать guardrails
- Не возвращать произвольный текст в JSON ролях

## NeedContext Contract

При недостатке контекста роль ДОЛЖНА вернуть:

```json
{"error": "NeedContext", "missing": ["required_item1", "required_item2"]}
```

Без дополнительного текста или пояснений.