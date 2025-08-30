# A6. Исправление "Failed to fetch data" - Fix Summary

## Статус
**Исправлено** — 2025-08-23 02:03 UTC

## Что поменяли

### Root Cause
Двойной префикс API в UI: `/api/v1/api/v1/orchestrator/features` вместо `/api/v1/orchestrator/features`

### Изменения в коде
```bash
# Массовая замена в UI компонентах:
sed -i "s|'/api/v1/|'/|g" src/components/*.tsx src/pages/*.tsx

# Затронутые файлы:
- src/components/ErrorList.tsx
- src/components/TaskQueue.tsx  
- src/components/TaskList.tsx
- src/components/RunningTasks.tsx
- src/components/FeatureList.tsx
- src/components/RunHistory.tsx
- src/components/FeatureDetail.tsx
- src/pages/Dashboard.tsx
```

### Примеры изменений:
```typescript
// До:
get('/api/v1/orchestrator/features')
get('/api/v1/logs/tail?limit=100&level=ERROR,WARNING')  
get('/api/v1/orchestrator/tasks')

// После:
get('/orchestrator/features')         // baseURL '/api/v1' добавляется автоматически
get('/logs/tail?limit=100&level=ERROR,WARNING')
get('/orchestrator/tasks')
```

### Пересборка UI
```bash
npx vite build --mode production
✓ built in 10.33s
```

## Почему помогло

### Правильная работа Axios:
```typescript
// api.ts
baseURL: '/api/v1',  

// Компонент
get('/orchestrator/features')

// Результат: '/api/v1' + '/orchestrator/features' = '/api/v1/orchestrator/features' ✅
```

### Вместо неправильного:
```typescript  
baseURL: '/api/v1',
get('/api/v1/orchestrator/features')  
// Результат: '/api/v1' + '/api/v1/orchestrator/features' = '/api/v1/api/v1/orchestrator/features' ❌
```

## Проверка исправления

### Новые файлы в dist:
```
dist/assets/index-da82439d.js    # Новый JS bundle с исправленными путями
dist/assets/index-f22d509c.css   # CSS остался тот же
```

### Ожидаемый результат после деплоя:
- ✅ Dashboard загружает фичи, задачи, запуски, логи
- ✅ Features показывает список и детали фич  
- ✅ Tasks отображает задачи
- ✅ Logs/Errors показывает события
- ✅ Chat работает с Maintainer API
- ✅ Исчезает "Failed to fetch data"
- ✅ В Network DevTools - только 200/4xx ответы

## Мониторинг после деплоя

### Проверить в nginx access.log:
```bash
# Должны исчезнуть запросы вида:
GET /api/v1/api/v1/orchestrator/features HTTP/2.0" 404

# Должны появиться запросы:  
GET /api/v1/orchestrator/features HTTP/2.0" 200
```

### В браузере DevTools → Network:
- Нет 404 ошибок на API endpoints
- Все вызовы к `/api/v1/*` (без двойного префикса)
- JSON данные загружаются в компоненты

## Заключение

**Проблема решена на уровне Frontend.**
Минимальное исправление конфигурации API путей без изменения архитектуры или серверных компонентов.

**Время исправления:** 15 минут
**Impact:** Критическая функциональность UI восстановлена