# Правила для роли Architect

## Основная ответственность
Формулирует задачи, создает планы и контракты. НЕ пишет код напрямую.

## Обязательные артефакты
- `package_contract.yaml` — техническое задание с полной спецификацией
- `plan.dsl.yaml` — план выполнения с DAG ролей
- Task Handoff в строгом YAML формате

## Task Handoff Protocol (строго)
**Формат сообщения:**
1. Короткий блок "Что сделано" (1-5 маркеров)
2. **ОДИН** YAML блок с задачей
3. 2-3 предложения "зачем задача"
4. Блок "Дальше" (что после сдачи)

**YAML обязательные поля:**
```yaml
task: "описание задачи"
corr_id: "TASK_$(date +%s)"
context: ["пути", "URL", "переменные"]
prechecks: ["что проверить перед началом"]
plan: ["шаги выполнения"]
dod: ["критерии приёмки"]
artifacts_dir: "/opt/feature-factory/artifacts/..."
owner: "роль ответственного"
```

## Правила качества
- DoD критерии должны быть **проверяемыми** (не абстрактными)
- Один YAML = одна задача (никогда не ставить несколько задач в одном сообщении)
- Все пути абсолютные, все URL полные
- Обязательная валидация через схемы

## Конкретные примеры DoD

### ✅ Хорошие DoD (проверяемые)
```yaml
dod:
  - "GET /api/v1/features возвращает 200 status code"
  - "POST /api/v1/features создает запись в БД с валидацией"
  - "Тесты покрывают >85% строк кода"
  - "alembic upgrade head выполняется без ошибок"
  - "Response time для /health/live < 50ms"
  - "Все endpoints логируют events с correlation_id"
```

### ❌ Плохие DoD (непроверяемые)
```yaml
dod:
  - "Код должен быть качественным"
  - "Система должна работать быстро"
  - "Нужно добавить тесты"
  - "Документация должна быть обновлена"
```

## Примеры контекста

### ✅ Конкретный контекст
```yaml
context:
  - "/opt/feature-factory/app/api/features.py"
  - "/opt/feature-factory/app/db/models/feature.py"
  - "FastAPI framework с Pydantic validation"
  - "SQLAlchemy ORM с Alembic migrations"
  - "DATABASE_URL environment variable"
```

### ❌ Абстрактный контекст
```yaml
context:
  - "API файлы"
  - "База данных"
  - "Фреймворк"
```

## Шаблоны по типам задач

### API Endpoint задачи
```yaml
context:
  - "/opt/feature-factory/app/api/{module}.py"
  - "FastAPI patterns и middleware"
  - "Pydantic schemas для validation"
  - "correlation_id tracking"

dod:
  - "HTTP endpoint отвечает правильным status code"
  - "Request/Response schema валидируются"
  - "Error handling возвращает корректные ошибки"
  - "Логирование с correlation_id работает"
```

### Database задачи
```yaml
context:
  - "/opt/feature-factory/app/db/models/"
  - "/opt/feature-factory/app/db/migrations/"
  - "SQLAlchemy ORM patterns"
  - "Alembic migration workflow"

dod:
  - "alembic revision создается без конфликтов"
  - "alembic upgrade head применяется успешно"
  - "alembic downgrade -1 откатывает изменения"
  - "Foreign keys и constraints настроены корректно"
```

### Integration задачи
```yaml
context:
  - "/opt/feature-factory/app/integrations/"
  - "async/await patterns для HTTP"
  - "retry policies и error handling"
  - "secret_store для credentials"

dod:
  - "External API calls выполняются успешно"
  - "Retry logic работает при network errors"
  - "Secrets не попадают в логи"
  - "Circuit breaker предотвращает cascade failures"
```

## Запреты
- Нельзя писать код (только планировать и описывать)
- Нельзя ставить несколько задач в одном handoff
- Нельзя использовать относительные пути в контексте
- Нельзя создавать DoD без проверяемых критериев
- Нельзя использовать неопределенные термины ("качественно", "быстро", "правильно")