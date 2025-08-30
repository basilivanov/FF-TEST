
# Smoke Test Report: Cortex v2 Bootstrap
**Дата**: 2025-08-28 12:57:58
**Статус**: ERROR

## Сводка результатов
- **Всего тестов**: 6
- **Успешно**: 5 ✅
- **Предупреждения**: 0 ⚠️
- **Ошибки**: 1 ❌
- **Процент успеха**: 83.3%

## Детальные результаты

### file_structure ✅
**Статус**: success

**Детали**:
- Карта секретов:
  - exists: True
  - size: 2318
  - lines: 77
- Правила и анти-паттерны:
  - exists: True
  - size: 3812
  - lines: 139

### doctrine_content ✅
**Статус**: success

**Детали**:
- found_sections: ['КРИТИЧЕСКИЕ ЗАПРЕТЫ', 'ЗАПРЕЩЕНО', 'ПРАВИЛЬНО', 'IndentationError', 'uvicorn', 'Alembic', 'secret_store']
- missing_sections: []
- total_sections: 7
- found_count: 7

### credentials_content ✅
**Статус**: success

**Детали**:
- found_elements: ['secret_store.get_secret', 'admin.ui.username', 'admin.ui.password', 'database.url', 'НИКОГДА', 'hardcoded_password', 'from app.api.secrets import secret_store']
- missing_elements: []
- dangerous_patterns: []
- elements_coverage: 1.0

### packager_basic ✅
**Статус**: success

**Детали**:
- basic_task:
  - context_length: 7645
  - has_doctrine: True
  - has_security: False
  - expected_security: False

### security_detection ✅
**Статус**: success

**Детали**:
- test_cases: [{'name': 'admin_access', 'description': 'Получить доступ к админке', 'should_trigger': True, 'actually_triggered': True, 'correct': True}, {'name': 'password_reset', 'description': 'Сбросить пароль пользователя', 'should_trigger': True, 'actually_triggered': True, 'correct': True}, {'name': 'api_key_setup', 'description': 'Настроить API ключи для интеграции', 'should_trigger': True, 'actually_triggered': True, 'correct': True}, {'name': 'login_form', 'description': 'Создать форму логина', 'should_trigger': True, 'actually_triggered': True, 'correct': True}, {'name': 'regular_task', 'description': 'Создать компонент отображения данных', 'should_trigger': False, 'actually_triggered': False, 'correct': True}]
- accuracy: 1.0

### full_integration ❌
**Статус**: error

**Детали**:
- context_length: 10717
- found_sections: ['# ДОКТРИНА И ПРАВИЛА РАБОТЫ', '# КАРТА ДОСТУПА К СЕКРЕТАМ', '# Context Package', '## Meta', '## Task DSL']
- section_positions:
  - # ДОКТРИНА И ПРАВИЛА РАБОТЫ: 0
  - # КАРТА ДОСТУПА К СЕКРЕТАМ: 3843
  - # Context Package: 8830
  - ## Meta: 8849
  - ## Task DSL: 8945
- correct_order: True
- sections_coverage: 1.0
- content_checks:
  - doctrine_present: True
  - security_present: True
  - task_meta_present: False
  - anti_patterns_present: True

**Ошибки**:
- Не прошли проверки контента: ['task_meta_present']

## Рекомендации

⚠️ **Обнаружены проблемы, требующие внимания.**

### Критические проблемы:
- Не прошли проверки контента: ['task_meta_present']

## Следующие шаги

1. **Тестирование в боевых условиях**: Создать реальную задачу и проверить контекст
2. **Мониторинг**: Отслеживать логи `context_pack_built` для подтверждения работы
3. **Обратная связь**: Собирать отзывы агентов о полезности новых секций
4. **Расширение**: Добавить дополнительные правила по мере выявления паттернов

