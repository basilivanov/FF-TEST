# Каталог ролей в UI

## Общие положения

Admin UI должен предоставлять возможность просмотра уставов и промптов для каждой роли, а также отображать хэши промптов для контроля целостности.

## Макеты

### Список ролей

Страница отображает таблицу со всеми ролями:

| Роль       | Устав              | Промпт              | Хэш промпта                              | Дата обновления     | Действия        |
|------------|--------------------|---------------------|------------------------------------------|---------------------|-----------------|
| Architect  | charter link       | prompt link         | e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4 | 2025-08-25 12:00:00 | Test Call       |
| Dev        | charter link       | prompt link         | f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5 | 2025-08-25 12:00:00 | Test Call       |
| QA         | charter link       | prompt link         | a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6 | 2025-08-25 12:00:00 | Test Call       |
| Scribe     | charter link       | prompt link         | b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7 | 2025-08-25 12:00:00 | Test Call       |
| Maintainer | charter link       | prompt link         | c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8 | 2025-08-25 12:00:00 | Test Call       |

### Просмотр устава/промпта

При клике на ссылку устава или промпта открывается страница с содержимым документа и метаинформацией:

- Путь к файлу
- Хэш содержимого (SHA256)
- Дата последнего обновления
- Версия документа
- Список обязательных разделов (для промптов)

### Кнопка "Test Call"

Для каждой роли предусмотрена кнопка "Test Call", которая позволяет:
1. Выполнить тестовый вызов LLM с промптом роли
2. Посмотреть результаты вызова
3. Проверить время отклика и использование токенов

## Поля DTO для UI

```typescript
interface RoleDTO {
  role: string;                // Название роли
  charter_path: string;        // Путь к файлу устава
  prompt_path: string;         // Путь к файлу промпта
  prompt_sha256: string;       // Хэш содержимого промпта
  updated_at: string;          // Дата последнего обновления
  version: string;             // Версия документа
  required_sections?: string[]; // Обязательные разделы (для промптов)
}
```

## API эндпоинты

### Получение списка ролей

```
GET /admin/api/roles

Response:
[
  {
    "role": "Architect",
    "charter_path": "agents/charters/architect.md",
    "prompt_path": "agents/prompts/architect.md",
    "prompt_sha256": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
    "updated_at": "2025-08-25T12:00:00Z",
    "version": "1.0.0"
  }
]
```

### Получение содержимого устава/промпта

```
GET /admin/api/roles/{role}/{document_type}

Параметры:
- role: название роли (Architect, Dev, QA, Scribe, Maintainer)
- document_type: тип документа (charter, prompt)

Response:
{
  "content": "# Содержимое документа...",
  "path": "agents/prompts/architect.md",
  "sha256": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
  "updated_at": "2025-08-25T12:00:00Z",
  "version": "1.0.0"
}
```

### Тестовый вызов LLM

```
POST /admin/api/roles/{role}/test-call

Параметры:
- role: название роли (Architect, Dev, QA, Scribe, Maintainer)

Body:
{
  "input": "Тестовый ввод для проверки промпта"
}

Response:
{
  "output": "Результат выполнения промпта",
  "prompt_tokens": 1200,
  "completion_tokens": 2800,
  "total_tokens": 4000,
  "execution_time_ms": 1250
}
```