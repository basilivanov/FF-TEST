# Standard Output Formats

## Architect Output Format
```yaml
# Task breakdown with dependencies
tasks:
  - id: "task-001"
    type: "migration" 
    dependencies: []
    files: ["app/db/migrations/add_table.py"]
  - id: "task-002" 
    type: "api"
    dependencies: ["task-001"]
    files: ["app/api/endpoint.py", "tests/test_endpoint.py"]
```

## Developer Output Format
```yaml
files:
  - app/api/[endpoint_name].py
  - tests/test_[endpoint_name].py
package_contract:
  package_id: PKG-[FEATURE_ID]-v1
```

## Validator Output Format
```yaml
artifact_manifest:
  test_files:
    - tests/unit/test_[module].py
    - tests/integration/test_[feature].py
  coverage_target: 70
```

## Scribe Output Format
```yaml
artifact_manifest:
  documentation_updates:
    - docs/Architecture.md
    - CHANGELOG.md
  event: doc_updated
```

## Universal Principles
- **YAML** for manifest headers
- **Fenced code blocks** for actual content
- **Explicit file paths** (no wildcards)
- **Dependency specification** where applicable
- **Event tracking** for orchestration