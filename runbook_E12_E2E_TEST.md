# Runbook: E12 E2E Tests

## Обзор
Этот документ описывает процедуры для выполнения end-to-end тестов системы Feature Factory, включая два сценария:
- E12-A: Полный прогон фичи через систему
- E12-B: Выполнение отдельной задачи

## Предварительные требования

### 1. Доступ к системе
- Доступ к API оркестратора по HTTPS
- Учетные данные для BasicAuth
- Доступ к тестовой базе данных

### 2. Проверка готовности системы
```bash
# Проверка здоровья системы
curl -u "admin:password" https://etl-tst.chococraft.ru/api/v1/health

# Проверка доступности API оркестратора
curl -u "admin:password" https://etl-tst.chococraft.ru/api/v1/orchestrator/features
```

## Сценарий E12-A: E2E FEATURE

### Шаг 1: Создание фичи
```bash
curl -X POST "https://etl-tst.chococraft.ru/api/v1/orchestrator/features" \
  -H "Content-Type: application/json" \
  -u "admin:password" \
  -d '{
    "title": "E2E Test Feature Runbook",
    "intent": {
      "action": "test_e2e",
      "params": {
        "description": "End-to-end test feature for runbook validation"
      }
    }
  }'
```

Сохраните ID фичи из ответа.

### Шаг 2: Планирование фичи
```bash
curl -X POST "https://etl-tst.chococraft.ru/api/v1/orchestrator/features/{FEATURE_ID}/plan" \
  -u "admin:password"
```

Замените {FEATURE_ID} на ID созданной фичи.

### Шаг 3: Запуск графа
```bash
curl -X POST "https://etl-tst.chococraft.ru/api/v1/orchestrator/features/{FEATURE_ID}/run" \
  -u "admin:password"
```

Сохраните run_id из ответа.

### Шаг 4: Мониторинг выполнения
```bash
# Проверка статуса графа
curl "https://etl-tst.chococraft.ru/api/v1/orchestrator/graph/{RUN_ID}/status" \
  -u "admin:password"
```

Замените {RUN_ID} на run_id из шага 3. Повторяйте этот шаг до получения статуса DONE или FAILED.

### Шаг 5: Проверка результатов
```bash
# Проверка финального статуса фичи
curl "https://etl-tst.chococraft.ru/api/v1/orchestrator/features/{FEATURE_ID}" \
  -u "admin:password"

# Проверка артефактов в директории /tmp/{RUN_ID}/
ls -la /tmp/{RUN_ID}/

# Проверка событий в логах (пример)
grep "{RUN_ID}" /var/log/feature-factory/app.log | grep -E "(artifact_applied|index_updated|doc_updated)"
```

## Сценарий E12-B: E2E TASK

### Шаг 1: Создание фичи и планирование
```bash
# Создание фичи
curl -X POST "https://etl-tst.chococraft.ru/api/v1/orchestrator/features" \
  -H "Content-Type: application/json" \
  -u "admin:password" \
  -d '{
    "title": "E2E Test Task Runbook",
    "intent": {
      "action": "test_task",
      "params": {
        "description": "Task for testing individual execution"
      }
    }
  }'

# Планирование фичи
curl -X POST "https://etl-tst.chococraft.ru/api/v1/orchestrator/features/{FEATURE_ID}/plan" \
  -u "admin:password"
```

### Шаг 2: Получение списка задач
```bash
curl "https://etl-tst.chococraft.ru/api/v1/orchestrator/tasks" \
  -u "admin:password"
```

Найдите Dev-таску в списке и сохраните её ID.

### Шаг 3: Запуск графа для фичи
```bash
curl -X POST "https://etl-tst.chococraft.ru/api/v1/orchestrator/features/{FEATURE_ID}/run" \
  -u "admin:password"
```

Сохраните run_id из ответа.

### Шаг 4: Мониторинг выполнения узлов
```bash
# Получение статуса графа с деталями по узлам
curl "https://etl-tst.chococraft.ru/api/v1/orchestrator/graph/{RUN_ID}/status" \
  -u "admin:password"
```

Повторяйте этот шаг до завершения всех узлов.

### Шаг 5: Проверка результатов
```bash
# Проверка статуса конкретной задачи
curl "https://etl-tst.chococraft.ru/api/v1/orchestrator/tasks/{TASK_ID}" \
  -u "admin:password"

# Проверка артефактов
ls -la /tmp/{RUN_ID}/

# Проверка логов для конкретного узла Dev
grep "{TASK_ID}" /var/log/feature-factory/app.log | grep "Dev"
```

## Обработка ошибок

### 5xx ошибки
Если получены ошибки 5xx:
1. Проверьте логи приложения: `/var/log/feature-factory/app.log`
2. Проверьте доступность базы данных
3. Проверьте конфигурацию API оркестратора
4. При необходимости перезапустите сервис

### BudgetExceeded
Если получено сообщение о превышении бюджета:
1. Проверьте текущее использование токенов: `curl -u "admin:password" https://etl-tst.chococraft.ru/admin/tokens`
2. Дождитесь следующего дня или увеличьте бюджет
3. Задача должна перейти в статус WAIT_BUDGET и возобновиться автоматически

### Timeout ошибки
Если запросы не отвечают в течение 30 секунд:
1. Проверьте нагрузку на систему
2. Проверьте сетевые подключения
3. Проверьте статус LLM провайдеров

## Проверка логов

### Основные команды для проверки логов
```bash
# Просмотр последних 100 строк лога
tail -n 100 /var/log/feature-factory/app.log

# Поиск по run_id
grep "{RUN_ID}" /var/log/feature-factory/app.log

# Поиск ошибок
grep "ERROR" /var/log/feature-factory/app.log

# Поиск событий LLM
grep "llm_call" /var/log/feature-factory/app.log

# Поиск событий артефактов
grep -E "(artifact_applied|index_updated|doc_updated)" /var/log/feature-factory/app.log
```

## Очистка после тестов

### Удаление тестовых данных
```bash
# Удаление фич из базы данных (только для тестов!)
sqlite3 /opt/feature-factory/data/test.db "DELETE FROM features WHERE title LIKE '%Runbook%';"

# Удаление временных файлов
rm -rf /tmp/{RUN_ID}/
```

## Контрольный список

### Перед началом тестов
- [ ] Система запущена и доступна по HTTPS
- [ ] API оркестратора доступен
- [ ] Учетные данные BasicAuth настроены
- [ ] Тестовая база данных доступна

### После выполнения тестов
- [ ] Все фичи завершены со статусом DONE
- [ ] Нет ошибок 5xx в ответах API
- [ ] Артефакты созданы и применены
- [ ] События логируются корректно
- [ ] Логи LLM содержат информацию об использовании
- [ ] Бюджет не превышен
- [ ] Индексы и реестры обновлены

## Контакты поддержки
- Администратор системы: admin@chococraft.ru
- Разработчики: dev-team@chococraft.ru
- QA команда: qa-team@chococraft.ru