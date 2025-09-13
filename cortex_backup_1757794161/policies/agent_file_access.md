# Internal Policy: Agent File Access

<!-- FF-DocMeta
title: Agent File Access Policy
purpose: Определяет правила доступа агентов к файловой системе
owner: architect
lifecycle: active
last_review: 2025-08-30
-->

## Правила доступа для агентов

1. **Интерактивные агенты** пишут ТОЛЬКО в:
   - `/opt/feature-factory/artifacts/<task_id>/`
   - `/opt/feature-factory/logs/<task_id>/`

2. **SSOT** может быть обновлен ТОЛЬКО через роли:
   - `Scribe` - для документации
   - `Maintainer` - для конфигураций

3. **Запрещено**:
   - Прямая запись в `/opt/feature-factory/cortex/` обычными агентами
   - Создание файлов в `/opt/feature-factory/docs/` (кроме README.md)
   - Изменение файлов в runtime-каталогах без явного разрешения

## Исключения сканирования

Следующие каталоги исключены из сканирования:
- `node_modules`
- `.git`
- `.venv`
- `__pycache__`
- `.cache`