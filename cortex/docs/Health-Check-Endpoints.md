# Health Check Endpoints

## Overview

Feature Factory предоставляет три эндпоинта для проверки состояния здоровья системы:

- `GET /health/live` - проверка живости приложения
- `GET /health/ready` - проверка готовности приложения к работе
- `GET /health/deps` - проверка зависимостей (LLM CLI провайдеры)

## Endpoints

### GET /health/live

**Назначение:** Проверка живости приложения. Всегда возвращает 200, если приложение запущено.

**Ответ:**
```json
{
  "status": "ok",
  "component": "live"
}
```

**Коды ответов:**
- `200 OK` - приложение запущено

---

### GET /health/ready

**Назначение:** Проверка готовности приложения к работе. Проверяет:
- Подключение к базе данных
- Применение миграций Alembic
- Наличие индексных файлов

**Ответ при успехе:**
```json
{
  "status": "ok",
  "component": "ready",
  "checks": [
    {
      "status": "ok",
      "component": "database"
    },
    {
      "status": "ok", 
      "component": "migrations",
      "version": "abc123def456"
    },
    {
      "status": "ok",
      "component": "index_files"
    }
  ]
}
```

**Коды ответов:**
- `200 OK` - всегда (даже при ошибках компонентов)

---

### GET /health/deps

**Назначение:** Проверка зависимостей системы. Проверяет доступность CLI бинарников для LLM провайдеров с улучшенной валидацией путей.

**Ответ при успехе:**
```json
{
  "status": "ok",
  "component": "deps",
  "checks": [
    {
      "status": "ok",
      "component": "llm_cli",
      "providers": [
        {
          "provider": "qwen",
          "status": "ok",
          "path": "/usr/local/bin/qwen",
          "version": "qwen 1.0.0"
        },
        {
          "provider": "stub",
          "status": "ok",
          "path": "/usr/bin/python3",
          "version": "Python 3.12.3"
        }
      ],
      "working_providers": 2,
      "total_providers": 2
    }
  ]
}
```

**Коды ответов:**
- `200 OK` - всегда (даже при ошибках зависимостей)

## Конфигурация

LLM провайдеры настраиваются в файле `/opt/feature-factory/configs/llm_cli.yaml`:

```yaml
qwen:
  cmd: ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"]
  env: ["QWEN_API_KEY"]
  expects: "json"

stub:
  cmd: ["python3", "-c", "print('test')"]
  env: []
  expects: "json"
```

## Улучшенная валидация путей CLI

В рамках задачи E6-ROUTER-CLI-CFG-PATHS-DEV была реализована улучшенная валидация путей CLI провайдеров:

1. **Валидация путей к бинарным файлам:** Проверяется существование бинарных файлов CLI провайдеров.
2. **Проверка прав доступа:** Проверяется, что бинарные файлы имеют права на выполнение.
3. **Получение версий:** Для каждого провайдера пытается получить версию бинарного файла.
4. **Подробные сообщения об ошибках:** В случае проблем с провайдерами предоставляются детальные сообщения об ошибках.

Новый модуль `app/llm/cli_path_guard.py` обеспечивает безопасность и надежность CLI транспорта.

## Логирование

Все health check операции логируются с событием `healthcheck`:

```json
{
  "event": "healthcheck",
  "env": "test",
  "component": "health",
  "agent_role": "System",
  "correlation_id": "health-check",
  "kv": {
    "component": "ready",
    "status": "ok",
    "checks": [...]
  }
}
```
