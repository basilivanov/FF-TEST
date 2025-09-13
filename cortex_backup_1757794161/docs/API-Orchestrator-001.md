# API-Orchestrator-001: Спецификация API оркестратора

## Обзор

API оркестратора предоставляет интерфейс для управления фичами, планирования задач и запуска графов выполнения. 
Все эндпоинты находятся под префиксом `/api/v1/orchestrator`.

## Эндпоинты

### POST /api/v1/orchestrator/features

Создает новую фичу в системе.

**Request Body (JSON):**
```json
{
  "title": "string",
  "intent": "object or string or null",
  "priority": "integer"
}
```

**Идемпотентность:**
Комбинация `(title, env)` уникальна. При повторном запросе с теми же параметрами возвращается 200 с существующим feature_id и status.

**Response (200):**
```json
{
  "feature_id": "integer",
  "status": "NEW"
}
```

### POST /api/v1/orchestrator/features/{id}/plan

Вызывает Architect (через Router) для создания задач (DAG).

**Response (200):**
```json
{
  "feature_id": "integer",
  "tasks": [
    {
      "id": "integer",
      "role": "string",
      "status": "NEW"
    }
  ]
}
```

**Response (404):**
```json
{
  "error": "FEATURE_NOT_FOUND"
}
```

### POST /api/v1/orchestrator/features/{id}/run

Запускает новый граф выполнения для фичи или возобновляет существующий активный граф.

**Response (200):**
```json
{
  "run_id": "string",
  "state": "STARTED|RESUMED"
}
```

### GET /api/v1/orchestrator/graph/{run_id}/status

Получает статус выполнения графа.

**Response (200):**
```json
{
  "run_id": "string",
  "graph": "G1",
  "nodes": [
    {
      "name": "string",
      "state": "NEW|RUNNING|DONE|FAILED"
    }
  ]
}
```

## JSON Schema

### R0-FeatureCreated.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "feature_id": {
      "type": "integer"
    },
    "status": {
      "type": "string",
      "const": "NEW"
    }
  },
  "required": ["feature_id", "status"]
}
```

### R1-Plan.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "feature_id": {
      "type": "integer"
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer"
          },
          "role": {
            "type": "string"
          },
          "status": {
            "type": "string",
            "const": "NEW"
          }
        },
        "required": ["id", "role", "status"]
      }
    }
  },
  "required": ["feature_id", "tasks"]
}
```

### R2-Run.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "run_id": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["RUNNING", "DONE"]
    }
  },
  "required": ["run_id", "status"]
}
```

### R3-GraphStatus.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "run_id": {
      "type": "string"
    },
    "graph": {
      "type": "string",
      "const": "G1"
    },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "state": {
            "type": "string",
            "enum": ["NEW", "RUNNING", "DONE", "FAILED"]
          }
        },
        "required": ["name", "state"]
      }
    }
  },
  "required": ["run_id", "graph", "nodes"]
}
```

## Идемпотентность

- `POST /api/v1/orchestrator/features`: идемпотентен по `(title, env)`
- `POST /api/v1/orchestrator/features/{id}/plan`: идемпотентен по `feature_id` 
- `POST /api/v1/orchestrator/features/{id}/run`: идемпотентен по `feature_id`
- `GET /api/v1/orchestrator/graph/{run_id}/status`: идемпотентен по `run_id`

## Коды ошибок

- `400`: Неверный формат запроса
- `404`: Ресурс не найден (FEATURE_NOT_FOUND)
- `409`: Конфликт состояний
- `500`: Внутренняя ошибка сервера

## Журналы событий

Все вызовы API логируются с событиями:
- `api_call_start`: Начало API вызова
- `api_call_end`: Завершение API вызова
- `feature_created`: Создание фичи
- `plan_generated`: Генерация плана
- `graph_run_started`: Запуск графа
- `graph_status_queried`: Запрос статуса графа

Все логи содержат `correlation_id` для корреляции запросов.