# 🧪 Безопасное E2E тестирование Feature Factory

Этот набор инструментов позволяет проводить E2E тестирование без риска поломки основной системы.

## 🚀 Быстрый старт

### Простой безопасный тест (только чтение):
```bash
./scripts/e2e_safe_test.sh
```

### Тест с Python утилитами:
```bash
python3 ./scripts/e2e_utils.py
```

### Полный тест с созданием реальных данных:
```bash
FULL_TEST=true ./scripts/e2e_safe_test.sh
```

## 🛡️ Уровни безопасности

### 1. Safe Mode (по умолчанию)
- ✅ Тестирует только read-only endpoints
- ✅ Использует фиктивные данные для CI
- ✅ Не создаёт реальные PR или ветки
- ✅ Не меняет состояние системы

### 2. Full Test Mode
- ⚠️ Создаёт тестовые features и ветки
- ⚠️ Требует подтверждения пользователя
- ✅ Автоматически убирает все созданные ресурсы
- ✅ Защищает основные ветки (main, master)

## 📁 Структура файлов

```
scripts/
├── e2e_safe_test.sh      # Основной bash скрипт
├── e2e_utils.py          # Python утилиты с context manager
├── README_E2E.md         # Эта документация
.e2erc                    # Конфигурация E2E тестов
```

## ⚙️ Конфигурация

Отредактируйте `.e2erc` для настройки поведения:

```bash
# Режим работы: safe, full, mock
export E2E_MODE="safe"

# Автоматическая очистка
export E2E_CLEANUP_ENABLED="true"

# Защита веток
export E2E_SKIP_BRANCHES="main,master,develop"

# Лимиты безопасности  
export E2E_MAX_TEST_FEATURES="3"
export E2E_MAX_TEST_BRANCHES="2"
```

## 🔍 Что тестируется

### В Safe Mode:
- ✅ Health endpoint (`/health/live`)
- ✅ API endpoints для чтения (`/api/v1/orchestrator/*`)
- ✅ OpenAPI документация (`/openapi.json`)
- ✅ CI endpoint с фиктивными данными
- ✅ Доступность базы данных (только чтение)

### В Full Mode (дополнительно):
- ✅ Создание и удаление features
- ✅ Создание и удаление Git веток
- ✅ Полный цикл CI статусов
- ✅ Интеграция с GitHub (если настроена)

## 🧹 Автоматическая очистка

Все тесты автоматически убирают за собой:

- 🗑️ Созданные Git ветки (локально и на remote)
- 🗑️ Тестовые файлы
- 🗑️ Записи в базе данных (features)
- 🗑️ Временные директории

Очистка происходит даже при аварийном завершении теста.

## 📊 Отчёты

После каждого теста генерируется отчёт в формате JSON:

```json
{
  "test_id": "e2e_safe_1672531200",
  "timestamp": "2025-01-01T12:00:00Z",
  "status": "completed", 
  "created_resources": {
    "features": [123],
    "branches": ["e2e-safe-test-branch"],
    "files": ["test_file.md"]
  },
  "artifacts_dir": "/tmp/e2e_test_1672531200"
}
```

## 🚨 Обработка ошибок

### Если тест упал:
1. Автоматическая очистка всё равно выполнится
2. Проверьте логи в artifacts директории
3. Вручную убедитесь что Git ветки удалены: `git branch -a | grep e2e`

### Если очистка не сработала:
```bash
# Ручная очистка веток
git branch -D $(git branch | grep e2e)
git push origin --delete $(git branch -r | grep e2e | sed 's/origin\///')

# Ручная очистка features из БД  
sqlite3 /opt/feature-factory/data/test.db "DELETE FROM features WHERE title LIKE '%E2E%'"
```

## 🐛 Отладка

### Включить подробные логи:
```bash
export E2E_LOG_LEVEL="debug"
./scripts/e2e_safe_test.sh
```

### Сохранить все артефакты:
```bash
export E2E_SAVE_ARTIFACTS="true"
./scripts/e2e_safe_test.sh
```

### Пропустить внешние API:
```bash
export E2E_SKIP_EXTERNAL_APIS="true" 
./scripts/e2e_safe_test.sh
```

## 📝 Примеры использования

### CI/CD пайплайн:
```yaml
# .github/workflows/e2e.yml
- name: Run safe E2E tests
  run: |
    cd /opt/feature-factory
    ./scripts/e2e_safe_test.sh
```

### Pre-commit hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit
./scripts/e2e_safe_test.sh || exit 1
```

### Мониторинг:
```bash
# Cron job каждые 30 минут
*/30 * * * * /opt/feature-factory/scripts/e2e_safe_test.sh > /var/log/e2e.log 2>&1
```

## 🔧 Расширение

Для добавления новых тестов:

1. **В bash скрипте** - добавьте функцию `test_your_feature()`
2. **В Python утилите** - добавьте метод в класс `SafeE2ETester`
3. **Зарегистрируйте** ресурсы для автоочистки в `self.created_resources`

## ⚡ Performance

- Safe режим: ~10-30 секунд
- Full режим: ~1-3 минуты
- Потребление памяти: <50MB
- Сетевой трафик: <1MB

## 🤝 Поддержка

При проблемах:
1. Проверьте `.e2erc` конфигурацию
2. Запустите с `E2E_LOG_LEVEL="debug"`
3. Проверьте artifacts директорию
4. Убедитесь что сервисы запущены