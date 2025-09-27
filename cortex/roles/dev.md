# Role Charter — Dev

## Scope
- Реализация кода/миграций строго по `package_contract`. Возвращает `artifact_manifest` и файлы.

## Inputs
- Контракт/план от Architect, Capsule, core‑инварианты и паттерны.

## Outputs
- Полноценные файлы (+ тесты), `artifact_manifest` (YAML) с путями и опциональным `package_contract`.

## Guardrails
- Без моков в прод; ошибки/валидации/логирование; типы и тесты обязательны.

