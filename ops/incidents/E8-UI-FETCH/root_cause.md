# Root Cause Analysis - "Failed to fetch data" в админке

## Статус
**Определен** — 2025-08-23 01:59 UTC

## Краткое резюме
**Проблема:** UI генерирует запросы с двойным префиксом `/api/v1/api/v1/...` вместо `/api/v1/...`

## Root Cause
**Некорректная конфигурация Axios baseURL в UI**

### Текущая (неправильная) логика:
```typescript
// src/lib/api.ts
const apiClient = axios.create({
  baseURL: '/api/v1',  // Базовый URL
})

// В компонентах UI:
get('/api/v1/orchestrator/features')  // Путь уже содержит префикс

// Результат конкатенации:
// baseURL + path = '/api/v1' + '/api/v1/orchestrator/features' 
//                = '/api/v1/api/v1/orchestrator/features' ❌
```

### Доказательства из логов:
```
85.174.201.52 - ops [23/Aug/2025:04:51:11] "GET /api/v1/api/v1/orchestrator/features HTTP/2.0" 404
85.174.201.52 - ops [23/Aug/2025:04:54:44] "GET /api/v1/api/v1/logs/tail?limit=100&level=ERROR,WARNING HTTP/2.0" 404
```

## Место разрыва
**Слой:** Frontend (UI configuration)  
**Файлы:** 
- `/opt/feature-factory/app/ui/src/lib/api.ts` (конфигурация Axios)
- Все компоненты UI, которые вызывают `get('/api/v1/...')` вместо `get('/...')`

## Impact
- ✅ Nginx/Proxy: работает корректно  
- ✅ Backend API: отвечает на правильные пути
- ✅ Authentication: BasicAuth проходит
- ❌ UI: генерирует неправильные URL

## Масштаб проблемы
**Затронутые эндпоинты:**
- Dashboard: загрузка фич, задач, запусков, логов
- Features: список фич, детали, планирование, запуск  
- Tasks: список задач
- Logs: просмотр ошибок
- Chat: Maintainer интеграция

**Пользовательский опыт:**
- "Failed to fetch data" во всех компонентах UI
- Retry/polling каждые 5 секунд с той же ошибкой
- UI остается функциональным, но без данных

## Исправление
**Требуется изменить пути в UI компонентах:**

### Вариант 1 (рекомендуемый): Исправить пути в компонентах
```typescript  
// Вместо:
get('/api/v1/orchestrator/features')

// Использовать:
get('/orchestrator/features')  // baseURL добавится автоматически
```

### Вариант 2: Изменить baseURL
```typescript
// src/lib/api.ts
const apiClient = axios.create({
  baseURL: '',  // Убрать базовый префикс
})
// Оставить пути как есть: get('/api/v1/orchestrator/features')
```

## Приоритет
**High** - критическая функциональность админки не работает

## Время исправления
**~15 минут** - массовая замена путей в компонентах UI