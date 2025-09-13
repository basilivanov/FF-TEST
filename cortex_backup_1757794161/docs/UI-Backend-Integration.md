# UI-Backend Integration Guide

## Обзор

Этот документ описывает интеграцию пользовательского интерфейса Feature Factory Admin UI с бэкендом.

## API эндпоинты

### Orchestrator API

#### GET /api/v1/orchestrator/features

Получение списка фич.

**Response:**
```json
[
  {
    "id": 1,
    "title": "Feature Title",
    "intent_json": {"action": "create"},
    "status": "NEW",
    "priority": 1,
    "created_at": "2023-01-01T00:00:00Z",
    "created_by": "user",
    "env": "test"
  }
]
```

#### POST /api/v1/orchestrator/features

Создание новой фичи.

**Request:**
```json
{
  "title": "New Feature",
  "intent_json": {"action": "create"}
}
```

**Response:**
```json
{
  "id": 1,
  "status": "NEW"
}
```

#### POST /api/v1/orchestrator/features/{id}/plan

Генерация плана для фичи.

**Response:**
```json
{
  "feature_id": 1,
  "tasks": [
    {
      "id": 1,
      "role": "Dev",
      "status": "NEW"
    }
  ],
  "package_contract": {}
}
```

#### POST /api/v1/orchestrator/features/{id}/run

Запуск выполнения фичи.

**Response:**
```json
{
  "run_id": "run-001",
  "state": "STARTED"
}
```

#### GET /api/v1/orchestrator/graph/{run_id}/status

Получение статуса запуска графа.

**Response:**
```json
{
  "run_id": "run-001",
  "graph": "G1",
  "status": "RUNNING",
  "last_checkpoint": "2023-01-01T00:00:00Z"
}
```

### Maintainer API

#### POST /api/v1/maintainer/intent

Генерация интента из естественного языка.

**Request:**
```json
{
  "nl_text": "Create a new feature"
}
```

**Response:**
```json
{
  "nl_text": "Create a new feature",
  "intent_json": {"action": "create"},
  "issues": [],
  "suggestions": []
}
```

#### POST /api/v1/maintainer/plan

Генерация плана из интента.

**Request:**
```json
{
  "intent_json": {"action": "create"}
}
```

**Response:**
```json
{
  "intent_json": {"action": "create"},
  "dag": [
    {
      "id": "task-001",
      "name": "task1",
      "kind": "code",
      "role": "Dev",
      "preconditions": [],
      "postconditions": [],
      "idempotency_key": "dev.task1.v1",
      "retry": {"max": 2, "backoff": "exp:5,30,120"},
      "deadline": "PT10M",
      "models": ["qwen", "gemini"],
      "outputs": ["files"],
      "dod": [],
      "severity": "high"
    }
  ],
  "package_contract": {}
}
```

### Stream API

#### GET /api/v1/stream/events

Получение потока событий в реальном времени через Server-Sent Events.

**Events:**
- `job_started`
- `job_finished`
- `error`
- `index_updated`
- `doc_updated`
- `llm_call_end`

### Logs API

#### GET /api/v1/logs/tail

Получение последних записей логов.

**Query Parameters:**
- `limit`: количество записей (по умолчанию 100)
- `component`: фильтр по компоненту
- `level`: фильтр по уровню лога
- `event`: фильтр по событию
- `agent_role`: фильтр по роли агента

**Response:**
```json
[
  {
    "ts": "2023-01-01T00:00:00Z",
    "level": "INFO",
    "env": "test",
    "component": "api",
    "agent_role": "Orchestrator",
    "run_id": "run-001",
    "task_id": "task-001",
    "correlation_id": "corr-001",
    "event": "job_started",
    "kv": {"job_id": "job-001"}
  }
]
```

### Tokens API

#### GET /admin/tokens

Получение статистики расхода токенов.

**Response:**
```json
[
  {
    "role": "Dev",
    "model": "qwen-plus",
    "input_tokens": 1000,
    "output_tokens": 500,
    "total_tokens": 1500,
    "cost": 0.015
  }
]
```

## Аутентификация

Доступ к API защищен Basic Auth. Учетные данные передаются в заголовке `Authorization`.

## Корреляция запросов

Все запросы к API должны содержать заголовок `X-Request-ID` для корреляции логов.

## Обработка ошибок

API возвращает стандартные HTTP коды ошибок:
- 400: Некорректный запрос
- 401: Неавторизованный доступ
- 404: Ресурс не найден
- 500: Внутренняя ошибка сервера

Тело ответа при ошибке:
```json
{
  "error": "ERROR_CODE",
  "detail": "Подробное описание ошибки"
}
```

## Rate Limiting

API может применять ограничения на количество запросов. При превышении лимита возвращается код 429.

## Кэширование

Некоторые эндпоинты поддерживают кэширование. Заголовок `Cache-Control` указывает на политику кэширования.

## CORS

API настроен на работу с доменами etl-tst.chococraft.ru и etl.chococraft.ru.

## WebSocket соединения

Для реал-тайм обновлений используется Server-Sent Events (SSE) по адресу `/api/v1/stream/events`.

## Пагинация

Для эндпоинтов, возвращающих списки данных, может применяться пагинация. Параметры:
- `limit`: количество элементов на странице
- `offset`: смещение от начала списка

## Фильтрация и сортировка

Некоторые эндпоинты поддерживают фильтрацию и сортировку через query параметры.

## Примеры интеграции

### Получение списка фич

```typescript
import { get } from '@/lib/api'

const features = await get<Feature[]>('/orchestrator/features')
```

### Создание фичи

```typescript
import { post } from '@/lib/api'

const newFeature = await post<Feature>('/orchestrator/features', {
  title: 'New Feature',
  intent_json: { action: 'create' }
})
```

### Подписка на поток событий

```typescript
import { sseClient } from '@/lib/sse'

sseClient.connect('/stream/events')
sseClient.on('job_started', (data) => {
  console.log('Job started:', data)
})
```

### Получение логов

```typescript
import { get } from '@/lib/api'

const logs = await get<LogEntry[]>('/logs/tail?limit=50&component=api')
```

## Мониторинг

### Health Checks

#### GET /api/v1/health

Проверка состояния API.

**Response:**
```json
{
  "status": "ok"
}
```

### Метрики

API предоставляет метрики для мониторинга:
- Время отклика
- Количество запросов
- Количество ошибок
- Использование ресурсов

## Логирование

Все запросы к API логируются с использованием стандартного формата логов Feature Factory.

## Безопасность

### Шифрование

Все соединения с API должны использовать HTTPS.

### Валидация данных

Все входные данные валидируются на стороне сервера.

### Санитизация

Все выходные данные санитизируются для предотвращения XSS атак.

## Производительность

### Оптимизация запросов

API оптимизирован для минимизации количества запросов и объема передаваемых данных.

### Кэширование на клиенте

Клиент может кэшировать ответы API для улучшения производительности.

### Lazy Loading

Данные загружаются по мере необходимости для уменьшения начального времени загрузки.

## Отладка

### Логи запросов

Все запросы к API логируются с подробной информацией для отладки.

### Инструменты разработчика

Для отладки API можно использовать инструменты разработчика в браузере или Postman.

## Best Practices

1. **Всегда обрабатывайте ошибки**
2. **Используйте корреляционные ID для отслеживания запросов**
3. **Кэшируйте данные при возможности**
4. **Используйте пагинацию для больших списков**
5. **Фильтруйте данные на стороне сервера**
6. **Обрабатывайте rate limiting**
7. **Используйте HTTPS для всех запросов**
8. **Валидируйте данные перед отправкой**