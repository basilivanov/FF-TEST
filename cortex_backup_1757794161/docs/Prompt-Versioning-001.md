# Правила пиннинга промптов по prompt_sha256 + rollback

## Общие положения

Для обеспечения стабильности и предсказуемости работы системы все промпты агентов версионируются с использованием SHA256 хэшей. Это позволяет гарантировать, что каждый узел графа использует именно ту версию промпта, которая была протестирована и утверждена.

## Механизм версионирования

### Хэширование промптов

Каждый промпт хэшируется с использованием алгоритма SHA256. Хэш вычисляется от полного содержимого файла промпта, включая все пробелы и символы новой строки.

Пример вычисления хэша:
```bash
sha256sum agents/prompts/architect.md
```

### Файл блокировки версий

Все хэши промптов хранятся в файле `configs/prompts.lock.json`, который выполняет роль блокировки версий (lock file). Этот файл генерируется автоматически при каждом изменении промптов и должен коммититься в репозиторий.

Формат файла:
```json
{
  "roles": {
    "Architect": {
      "file": "agents/prompts/architect.md",
      "sha256": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
      "updated_at": "2025-08-25T15:00:00Z"
    },
    "Dev": {
      "file": "agents/prompts/dev.md",
      "sha256": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
      "updated_at": "2025-08-25T15:00:00Z"
    },
    "QA": {
      "file": "agents/prompts/qa.md",
      "sha256": "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8",
      "updated_at": "2025-08-25T15:00:00Z"
    },
    "Scribe": {
      "file": "agents/prompts/scribe.md",
      "sha256": "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9",
      "updated_at": "2025-08-25T15:00:00Z"
    },
    "Maintainer": {
      "file": "agents/prompts/maintainer.md",
      "sha256": "c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0",
      "updated_at": "2025-08-25T15:00:00Z"
    }
  }
}
```

## Валидация при запуске Orchestrator

При старте Orchestrator выполняет валидацию промптов:

1. Загружает файл `configs/prompts.lock.json`
2. Для каждой роли читает соответствующий файл промпта
3. Вычисляет SHA256 хэш содержимого файла
4. Сравнивает вычисленный хэш с хэшем из файла блокировки
5. При несовпадении генерирует событие `prompt_drift_detected` и блокирует узлы Dev/QA

### Событие prompt_drift_detected

При обнаружении расхождения хэшей генерируется следующее событие:
```json
{
  "event": "prompt_drift_detected",
  "role": "Dev",
  "expected_sha256": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
  "actual_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "file_path": "agents/prompts/dev.md",
  "timestamp": "2025-08-25T16:00:00Z"
}
```

### Блокировка узлов

При обнаружении дрейфа промптов Orchestrator блокирует узлы Dev и QA, генерируя событие Gate REJECT с кодом PROMPT_DRIFT:
```json
{
  "event": "artifact_rejected",
  "reason": "PROMPT_DRIFT",
  "role": "Dev",
  "details": "Prompt drift detected for role Dev",
  "expected_sha256": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
  "actual_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "task_id": "task_12345"
}
```

## Процедура обновления промптов

### 1. Внесение изменений

1. Отредактируйте файл промпта
2. Убедитесь, что изменения соответствуют структуре и формату
3. Проверьте, что все обязательные разделы присутствуют

### 2. Пересчет хэшей

1. Вычислите SHA256 хэш измененного файла:
   ```bash
   sha256sum agents/prompts/architect.md
   ```
2. Обновите соответствующую запись в `configs/prompts.lock.json`
3. Укажите текущую дату и время в поле `updated_at`

### 3. Тестирование

1. Запустите тесты для проверки совместимости изменений
2. Убедитесь, что все QA-проверки проходят успешно
3. Проверьте, что система корректно загружает обновленный промпт

### 4. Коммит изменений

1. Зафиксируйте изменения в репозитории:
   ```bash
   git add agents/prompts/architect.md configs/prompts.lock.json
   git commit -m "Обновление промпта Architect: описание изменений"
   git push origin main
   ```

## Процедура отката (rollback)

### Автоматический откат

В случае обнаружения проблем с новой версией промпта можно выполнить автоматический откат:

1. Orchestrator обнаруживает проблему (например, высокий уровень REJECT)
2. Система автоматически переключается на предыдущую версию промпта из резервной копии
3. Генерируется событие `prompt_rollback_executed`

### Ручной откат

Для ручного отката выполните следующие шаги:

1. Найдите предыдущую версию файла промпта в истории Git:
   ```bash
   git log --oneline agents/prompts/architect.md
   git show COMMIT_HASH:agents/prompts/architect.md > agents/prompts/architect.md
   ```
2. Найдите соответствующую запись в `configs/prompts.lock.json` из истории
3. Восстановите хэш предыдущей версии
4. Пересчитайте хэш и обновите файл блокировки
5. Закоммитьте изменения

## Логирование

### prompt_lock_loaded

Событие генерируется при успешной загрузке файла блокировки:
```json
{
  "event": "prompt_lock_loaded",
  "roles_count": 5,
  "timestamp": "2025-08-25T16:00:00Z"
}
```

### prompt_drift_detected

Событие генерируется при обнаружении расхождения хэшей (описано выше)

### prompt_rollback_executed

Событие генерируется при выполнении отката:
```json
{
  "event": "prompt_rollback_executed",
  "role": "Architect",
  "from_sha256": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
  "to_sha256": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
  "reason": "High reject rate detected",
  "timestamp": "2025-08-25T16:30:00Z"
}
```

## Best Practices

1. Всегда обновляйте `configs/prompts.lock.json` при изменении промптов
2. Не редактируйте файл блокировки вручную - используйте автоматические инструменты
3. Регулярно проверяйте целостность хэшей в CI pipeline
4. Сохраняйте историю изменений промптов в Git
5. Тестируйте изменения промптов перед их применением в production