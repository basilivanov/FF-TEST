# A4. Сопоставление путей UI ↔ API

## Статус  
**Создано** — 2025-08-23 01:55 UTC

## Анализ базового префикса API

### Конфигурация в api.ts
```typescript
// src/lib/api.ts:5
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})
```

### Конфигурация в sse.ts  
```typescript
// src/lib/sse.ts:9
constructor(baseUrl?: string) {
  this.BASE_URL = baseUrl || import.meta.env.VITE_API_BASE_URL || '/api/v1'
}
```

### Фактическое значение PREFIX
✅ **Базовый префикс:** `/api/v1` (fallback, так как VITE_API_BASE_URL не установлена)  
✅ **Единый префикс:** Axios и SSE используют один и тот же базовый путь  
✅ **Относительные пути:** Все вызовы используют относительные URL, начинающиеся с `/`

## Список вызываемых путей в UI

### Dashboard компонент
```typescript
// src/pages/Dashboard.tsx
'/api/v1/orchestrator/features'     → получение фич
'/api/v1/orchestrator/tasks'        → получение задач
'/api/v1/orchestrator/runs'         → получение запусков графов
'/api/v1/logs/tail?limit=5'         → последние логи
```

### Feature Management
```typescript  
// src/components/FeatureList.tsx
'/api/v1/orchestrator/features'                     → список фич

// src/components/FeatureDetail.tsx
'/api/v1/orchestrator/features/{id}'                → детали фичи
'/api/v1/orchestrator/features/{id}/tasks'          → задачи фичи
'/api/v1/orchestrator/features/{id}/runs'           → запуски фичи
'/api/v1/orchestrator/features/{id}/plan'  [POST]   → планирование
'/api/v1/orchestrator/features/{id}/run'   [POST]   → запуск
```

### Task Management
```typescript
// src/components/TaskList.tsx, TaskQueue.tsx, RunningTasks.tsx
'/api/v1/orchestrator/tasks'                        → список задач
'/api/v1/orchestrator/tasks/{id}/retry'    [POST]   → повтор задачи (закомментировано)
'/api/v1/orchestrator/tasks/{id}/pause'    [POST]   → пауза задачи (закомментировано)
```

### Logs and Monitoring
```typescript
// src/components/ErrorList.tsx, RunningTasks.tsx, Dashboard.tsx
'/api/v1/logs/tail?limit=100&level=ERROR,WARNING'   → логи ошибок
'/api/v1/logs/tail?limit=10'                        → последние события
'/api/v1/logs/tail?limit=5'                         → логи для дашборда
```

### Runs History
```typescript
// src/components/RunHistory.tsx  
'/api/v1/orchestrator/runs'                         → история запусков графов
```

### SSE Stream
```typescript
// src/lib/sse.ts используется для:
'/stream/events'                                     → SSE поток (добавляется к baseURL)
// Результат: /api/v1/stream/events
```

## Проверка консистентности путей

### ✅ Все пути начинаются с единого префикса
- Базовый URL: `/api/v1` 
- Все компоненты используют относительные пути
- Нет абсолютных URL на другие домены

### ✅ Нет конфликтующих префиксов
- Нет вызовов к `/api` (без версии)
- Нет смешения `/api/v1` и `/api/v2`
- Все пути соответствуют одной схеме

### ✅ Credentials не требуются
- Axios не использует `credentials: 'include'` 
- BasicAuth идет через заголовки Authorization
- Нет cookie-based аутентификации

## Фактические эндпоинты vs существующие API

### Существующие (проверенные в A3)
✅ `/api/v1/orchestrator/features` — работает  
✅ `/api/v1/maintainer/intent` — работает  
✅ `/api/v1/stream/events` — работает  

### Ожидаемые UI, но возможно не реализованные
⚠️ `/api/v1/orchestrator/tasks` — нужна проверка  
⚠️ `/api/v1/orchestrator/runs` — нужна проверка  
⚠️ `/api/v1/orchestrator/features/{id}` — нужна проверка  
⚠️ `/api/v1/orchestrator/features/{id}/tasks` — нужна проверка  
⚠️ `/api/v1/logs/tail` — нужна проверка (используется `/admin/logs`)

## Environment Variables Check

### .env файлы
```bash
$ find /opt/feature-factory/app/ui -name "*.env*" -o -name ".env*"
# Нет .env файлов найдено
```

### Vite конфигурация
```typescript
// vite.config.ts не содержит define для VITE_API_BASE_URL
// Используется fallback значение '/api/v1'
```

## Заключение A4

**Конфигурация UI корректна:**

✅ **Единый префикс:** `/api/v1` для всех компонентов  
✅ **Относительные пути:** Нет кросс-доменных запросов  
✅ **Нет credentials:** BasicAuth через заголовки, не через cookies  
✅ **Консистентность:** Axios и SSE используют один baseURL  

**Потенциальные проблемы:**

⚠️ **API Gap:** UI ожидает эндпоинты которые могут быть не реализованы:
- `/api/v1/orchestrator/tasks` 
- `/api/v1/orchestrator/runs`
- `/api/v1/logs/tail` (вместо `/admin/logs`)

**Рекомендация:** Проверить доступность всех API эндпоинтов, которые UI пытается вызвать.