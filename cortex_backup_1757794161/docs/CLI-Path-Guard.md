# CLI Path Guard

## Обзор

Модуль `cli_path_guard.py` обеспечивает валидацию путей к CLI бинарным файлам провайдеров LLM, проверку прав доступа и получение версий бинарных файлов. Это улучшает безопасность и надежность CLI транспорта.

## Функции

### validate_cli_paths()

Валидирует пути к CLI бинарным файлам для всех провайдеров.

**Возвращает:**
`Dict[str, Dict[str, Any]]` - Результаты валидации для каждого провайдера

**Пример результата:**
```python
{
    "qwen": {
        "status": "ok",
        "path": "/usr/local/bin/qwen",
        "version": "qwen 1.0.0"
    },
    "stub": {
        "status": "ok",
        "path": "/usr/bin/python3",
        "version": "Python 3.12.3"
    }
}
```

### get_health_check_result()

Получает результат health check для CLI зависимостей.

**Возвращает:**
`Dict[str, Any]` - Результат health check

**Пример результата:**
```python
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
```

### check_cli_dependencies()

Проверяет зависимости CLI для интеграции с health check endpoints.

**Возвращает:**
`Tuple[bool, str]` - (успех, сообщение)

**Пример результата:**
```python
(True, "All 2 CLI providers are valid")
```

## Использование

Модуль автоматически интегрирован в health check endpoint `GET /health/deps` и используется для проверки зависимостей CLI провайдеров.

## Исключения

### CliPathError

Базовый класс для ошибок путей CLI.

### CliBinaryNotFoundError

Ошибка, когда бинарный файл CLI не найден.

### CliPermissionError

Ошибка прав доступа к бинарному файлу CLI.

### CliConfigError

Ошибка в конфигурации CLI.