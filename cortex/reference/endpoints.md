# API Endpoints Reference

## Base URLs
- **TEST:** `http://127.0.0.1:8081/api/v1`
- **Production:** `https://etl.chococraft.ru/api/v1`

## Authentication
- **Basic Auth:** `ops:ops123` для CI endpoints
- **Headers:** `X-Correlation-Id` обязательный

## Health & Monitoring

### GET /health/live
Liveness probe - базовая проверка работоспособности
**Response:** `{"status": "ok"}`

### GET /health/ready  
Readiness probe - проверка готовности к обработке запросов
**Response:** `{"status": "ok"}`

### GET /api/v1/metrics
Prometheus метрики в text формате

### GET /api/v1/logs/stream
Server-Sent Events поток логов
**Content-Type:** `text/event-stream`

## CI Integration

### POST /api/v1/ci/webhook
GitHub webhook для CI событий
**Auth:** HMAC SHA-256 с `X-Hub-Signature-256`

### POST /api/v1/ci/status
Публикация статусов CI проверок
**Auth:** Basic `ops:ops123`
**Body:**
```json
{
  "context": "lint|tests|build|smoke",
  "state": "success|failure|pending", 
  "description": "Status description"
}
```

## Orchestrator

### POST /api/v1/orchestrator/features
Создание новой фичи
**Body:**
```json
{
  "title": "Feature title",
  "intent": {},
  "autostart": true
}
```

### POST /api/v1/runner/run-once
Однократный запуск runner'а
**Auth:** Basic `ops:ops123`

### GET /api/v1/features/{id}/graph
Граф выполнения фичи

### GET /api/v1/tasks/{id}
Информация о задаче

## Context & Documentation

### GET /.well-known/ff-context.json
Публичный контекст системы
**Cache-Control:** `public, max-age=60`
**Rate Limit:** 20 burst requests

### GET /api/v1/context-lite
Облегченный контекст для агентов

## Error Codes
- **200:** Success
- **400:** Bad Request  
- **401:** Unauthorized
- **404:** Not Found
- **429:** Rate Limited
- **500:** Internal Error

## Response Format
```json
{
  "error": "ERROR_CODE",
  "detail": "Detailed error description"
}
```