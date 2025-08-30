# E13-CI-E2E Implementation Guide

## Обзор

Данный документ описывает реализацию капсулы **E13-CI-E2E** — автоматического прогона E2E тестов (E12-A и E12-B) в CI/CD pipeline на каждом merge в main и по nightly расписанию.

## Цель

Автоматизировать регрессионное тестирование системы Feature Factory через:
- Автоматический запуск E2E тестов при merge в main
- Блокирование merge при падении тестов
- Nightly регрессия с публикацией отчётов
- Уведомления при падении тестов

## Архитектура решения

### 1. CI Pipeline (.github/workflows/e2e-regression.yml)

```yaml
name: E2E Regression Tests

triggers:
  - push to main
  - pull_request to main  
  - schedule: nightly (2:00 AM MSK)
  - manual dispatch

jobs:
  - feature_e2e    # E12-A тест
  - task_e2e       # E12-B тест
  - publish_nightly_report (только для schedule)
  - send_alert     # при падении тестов
```

### 2. E2E Test Scripts

#### Feature E2E (scripts/e2e_feature_test.py)
- Полный прогон фичи через систему
- Создание → Планирование → Выполнение → Мониторинг
- Строгие проверки: нет 5xx, статус DONE, логирование Logging-001

#### Task E2E (scripts/e2e_task_test.py)  
- Выполнение задачи через граф узлов
- Мониторинг узлов: Dev→Gate→QA→Scribe→Apply
- Проверка статуса задачи и артефактов

### 3. Отчётность

#### Автоматические отчёты (scripts/generate_e2e_report.py)
- Отчёт по каждому тесту с результатами
- Upload в CI artifacts
- Метрики времени выполнения

#### Nightly консолидированный отчёт (scripts/generate_nightly_report.py)
- Сводный отчёт за день
- Статус всех компонентов системы
- Рекомендации по деплою
- Публикация в docs/_bundle/

### 4. Branch Protection

#### GitHub Branch Protection Rules
- Обязательные status checks: feature_e2e, task_e2e
- Блокирование merge при падении тестов
- Требование PR approval
- Linear history

## Установка и настройка

### Шаг 1: Создание репозитория и базовой структуры

```bash
# Инициализация git (если не было)
git init
git branch -m main

# Создание структуры CI/CD
mkdir -p .github/workflows scripts

# Копирование файлов workflow и scripts
# (файлы уже созданы в проекте)
```

### Шаг 2: Настройка GitHub Secrets

В GitHub Settings → Secrets добавить:

```bash
# Для доступа к TEST окружению (если отличается от дефолтного)
TEST_URL = "https://etl-tst.chococraft.ru"
BASIC_AUTH_USER = "admin"  
BASIC_AUTH_PASS = "password"

# Для уведомлений Slack (опционально)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
```

### Шаг 3: Настройка Branch Protection

#### Автоматически через скрипт:
```bash
export GITHUB_TOKEN="your_token"
export GITHUB_REPOSITORY="owner/repo"
python scripts/setup_branch_protection.py
```

#### Вручную через GitHub UI:
1. Settings → Branches → Add rule для `main`
2. ☑️ Require status checks: `feature_e2e`, `task_e2e`
3. ☑️ Require pull request reviews
4. ☑️ Include administrators

### Шаг 4: Первый запуск

```bash
# Добавление файлов в git
git add .github/ scripts/ docs/
git commit -m "feat: добавить E13-CI-E2E автоматизацию

- GitHub Actions workflow для E2E регрессии
- Скрипты для автоматического тестирования E12-A и E12-B  
- Nightly отчёты и уведомления
- Branch protection для блокировки merge при падении E2E

🤖 Generated with Claude Code"

# Push и создание первого PR для тестирования
git push -u origin main
```

## Использование

### Автоматические запуски

1. **При Push в main**: автоматический запуск E2E тестов
2. **При создании PR**: проверка E2E перед merge
3. **Nightly (2:00 MSK)**: полная регрессия с отчётом
4. **Manual**: запуск через GitHub Actions UI

### Мониторинг результатов

#### В GitHub Actions:
- Статус тестов в PR checks
- Детальные логи выполнения
- Artifacts с отчётами

#### Отчёты в docs/_bundle/:
- `nightly_e2e_report_YYYY-MM-DD.md` - ночные отчёты
- Сводка по всем компонентам системы

#### Уведомления:
- Slack alerts при падении тестов
- Email notifications (через GitHub settings)

### Интерпретация результатов

#### ✅ Успешный прогон:
- Все API эндпоинты работают
- Граф узлов выполняется корректно
- Нет 5xx ошибок
- Логирование соответствует Logging-001

#### ❌ Падение тестов:
- Проверить логи в GitHub Actions
- Проверить доступность TEST окружения
- Проверить LLM провайдеры и бюджеты
- Исправить проблемы перед merge

## Обслуживание

### Регулярные задачи

#### Еженедельно:
- Проверка nightly отчётов
- Анализ трендов производительности
- Обновление тестовых сценариев

#### Ежемесячно:
- Очистка старых CI artifacts
- Обновление dependencies в скриптах
- Ревизия branch protection rules

### Устранение неполадок

#### Частые проблемы:

1. **Таймауты тестов**
   - Увеличить timeout в workflow
   - Проверить нагрузку на TEST окружение

2. **5xx ошибки**
   - Проверить статус API оркестратора
   - Проверить базу данных

3. **Превышение бюджета LLM**
   - Система должна корректно обрабатывать WAIT_BUDGET
   - Проверить конфигурацию бюджетов

4. **Branch protection не работает**
   - Проверить GITHUB_TOKEN permissions
   - Убедиться что status check names совпадают

## Расширение

### Добавление новых E2E сценариев

1. Создать новый скрипт в `scripts/`
2. Добавить job в `.github/workflows/e2e-regression.yml`
3. Обновить branch protection rules
4. Добавить в nightly отчёт

### Интеграция с другими системами

- **Мониторинг**: интеграция с Prometheus/Grafana
- **Уведомления**: дополнительные каналы (Teams, Discord)
- **Отчётность**: интеграция с системами трекинга качества

## DoD Compliance

### Выполненные требования E13-CI-E2E:

✅ **CI pipeline e2e-regression**: два джоба (feature_e2e, task_e2e)  
✅ **Блокирующий статус**: merge заблокирован при падении E2E  
✅ **Nightly расписание**: публикация отчёта в docs/_bundle/  
✅ **История запусков**: привязка к commit-id в CI  
✅ **Строгие проверки**: только 200/4xx и схематизация JSON  
✅ **Алерты при падении**: канал Slack и логирование событий  

### Логирование событий:

```json
{
  "event": "e2e_regression_started",
  "correlation_id": "uuid",
  "commit_id": "sha",
  "trigger": "push|schedule|manual"
}

{
  "event": "e2e_regression_finished", 
  "correlation_id": "uuid",
  "result": "success|failure",
  "duration_seconds": 120
}

{
  "event": "e2e_regression_nightly",
  "correlation_id": "uuid", 
  "report_file": "docs/_bundle/nightly_e2e_report_2025-08-22.md"
}
```

## Заключение

Реализация E13-CI-E2E обеспечивает:
- Автоматическую регрессию при каждом изменении
- Предотвращение деплоя нерабочего кода
- Непрерывный мониторинг качества системы
- Быструю диагностику проблем

Система готова к продакшену и соответствует всем требованиям DoD.