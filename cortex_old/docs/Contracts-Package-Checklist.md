# Минимум для Architect/Dev/QA/Scribe ответов

## Architect

### Обязательные элементы ответа

1. **Краткое резюме** (3-5 строк)
2. **package_contract.yaml** со следующими полями:
   - `package_id` (строка)
   - `summary` (строка)
   - `files_layout` (массив строк)
   - `db` (объект, опционально)
   - `index_api` (объект, опционально)
   - `logging` (объект, опционально)
   - `dod` (массив строк, опционально)
   - `budget` (объект, опционально)
3. **plan.dsl.yaml** с корректной структурой DAG
4. **Риски/допущения** (список)
5. **Сигнатура промпта**:
   - `prompt_id`: путь к файлу промпта
   - `prompt_sha256`: хэш содержимого промпта

### Пример валидного ответа Architect

```yaml
# package_contract.yaml
package_id: "PKG-001"
summary: "Добавление отчета продаж в UI"
files_layout:
  - "app/api/reports.py"
  - "app/ui/components/ReportCard.vue"
  - "tests/api/test_reports.py"

# plan.dsl.yaml
dag:
  tasks:
    - id: "DEV-001"
      role: "Dev"
      summary: "Реализация API отчетов"
    - id: "QA-001"
      role: "QA"
      summary: "Тестирование API отчетов"
      after: ["DEV-001"]
    - id: "SCRIBE-001"
      role: "Scribe"
      summary: "Документация API отчетов"
      after: ["QA-001"]

risks:
  - "Высокая нагрузка на БД при больших объемах данных"
  - "Зависимость от внешнего API поставщика данных"

prompt_id: "agents/prompts/architect.md"
prompt_sha256: "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6"
```

## Dev

### Обязательные элементы ответа

1. **Краткое резюме** (2-3 строки)
2. **artifact_manifest.yaml** со следующими полями:
   - `package_id` (строка)
   - `files` (массив объектов с полями path и content)
   - `dod` (массив строк, опционально)
3. **Файлы** в fenced-блоках с указанием путей
4. **Сигнатура промпта**:
   - `prompt_id`: путь к файлу промпта
   - `prompt_sha256`: хэш содержимого промпта

### Пример валидного ответа Dev

```yaml
# artifact_manifest.yaml
package_id: "PKG-001"
files:
  - path: "app/api/reports.py"
    content: |
      # Реализация API отчетов
      from fastapi import APIRouter
      # ...
  - path: "tests/api/test_reports.py"
    content: |
      # Тесты для API отчетов
      import pytest
      # ...

prompt_id: "agents/prompts/dev.md"
prompt_sha256: "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7"
```

## QA

### Обязательные элементы ответа

1. **Итог**: `PASS` или `FAIL`
2. **Таблица проверок** с полями:
   - `check`: название проверки
   - `result`: результат (PASS/FAIL)
   - `details`: детали проверки
3. **Метрики**:
   - Время выполнения
   - Покрытие критических веток
4. **Сигнатура промпта**:
   - `prompt_id`: путь к файлу промпта
   - `prompt_sha256`: хэш содержимого промпта

### Пример валидного ответа QA

```markdown
# Результаты QA

Итог: PASS

## Таблица проверок

| Проверка | Результат | Детали |
|---------|----------|--------|
| Валидность manifest | PASS | Все обязательные поля присутствуют |
| Пути файлов | PASS | Все пути корректны и находятся в tmp/{run_id}/ |
| Наличие секретов | PASS | Секреты не найдены |
| Логи LLM | PASS | Событие llm_call_end присутствует |

## Метрики

- Время выполнения: 2.5 сек
- Покрытие критических веток: 100%

prompt_id: agents/prompts/qa.md
prompt_sha256: a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8
```

## Scribe

### Обязательные элементы ответа

1. **CHANGELOG delta** блок
2. **Документы** в fenced-блоках с указанием путей
3. **Запись в doc_registry** в формате JSON
4. **Событие doc_updated** в логах
5. **Сигнатура промпта**:
   - `prompt_id`: путь к файлу промпта
   - `prompt_sha256`: хэш содержимого промпта

### Пример валидного ответа Scribe

```markdown
## [Unreleased]

### Added
- Добавлен API отчетов продаж в `app/api/reports.py`
- Добавлены тесты для API отчетов в `tests/api/test_reports.py`

# Запись в реестре документов

```json
{
  "doc_name": "docs/API-Reports.md",
  "version": "1.0.0",
  "content_hash": "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9",
  "updated_at": "2025-08-25T15:00:00Z"
}
```

prompt_id: agents/prompts/scribe.md
prompt_sha256: b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9
```