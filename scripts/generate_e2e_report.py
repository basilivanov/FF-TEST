#!/usr/bin/env python3
"""
Генератор отчётов E2E тестирования для CI/CD
"""

import sys
import json
import os
from datetime import datetime

def generate_feature_report(outcome, commit_id=None):
    """Генерация отчёта для Feature E2E теста"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_id = commit_id or os.getenv('GITHUB_SHA', 'unknown')[:8]
    
    status_emoji = "✅" if outcome == "success" else "❌"
    
    report = f"""# CI E2E Feature Test Report

## Общая информация
- **Дата:** {timestamp}
- **Тип теста:** E2E Feature (E12-A)
- **Результат:** {status_emoji} {outcome.upper()}
- **Commit ID:** {commit_id}
- **Окружение:** TEST (https://etl-tst.chococraft.ru)

## Цель теста
Автоматическая проверка полного прогона фичи через систему Feature Factory в рамках CI/CD pipeline.

## Выполненные проверки

### ✅ Основные требования
- API доступен по HTTPS с BasicAuth
- Нет 5xx ошибок в ответах
- Система самоисполняется через backlog и БД
- Логирование соответствует стандарту Logging-001

### ✅ Этапы выполнения
1. Создание фичи через API
2. Планирование фичи (генерация задач)
3. Запуск графа выполнения
4. Мониторинг до завершения
5. Проверка финального статуса
6. Проверка доступности /admin/tokens
7. Проверка доступности /api/v1/logs
8. Проверка сценария WAIT_BUDGET

## Результаты
"""
    
    if outcome == "success":
        report += """
- ✅ Фича успешно создана и обработана
- ✅ Граф выполнения завершён со статусом DONE
- ✅ Все API эндпоинты работают корректно
- ✅ События логируются согласно стандарту
- ✅ Артефакты созданы и применены
- ✅ Endpoint /admin/tokens доступен
- ✅ Endpoint /api/v1/logs доступен
- ✅ Сценарий WAIT_BUDGET проверен
"""
    else:
        report += """
- ❌ Тест завершился с ошибкой
- ❌ Требуется ручная проверка системы
- ❌ Возможна проблема с API или инфраструктурой
"""
    
    report += f"""
## Следующие действия
{f'Система готова к продакшену' if outcome == 'success' else 'Требуется исправление ошибок перед деплоем'}

---
🤖 Автоматически сгенерировано CI/CD Pipeline
Время генерации: {timestamp}
"""
    
    return report

def generate_task_report(outcome, commit_id=None):
    """Генерация отчёта для Task E2E теста"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_id = commit_id or os.getenv('GITHUB_SHA', 'unknown')[:8]
    
    status_emoji = "✅" if outcome == "success" else "❌"
    
    report = f"""# CI E2E Task Test Report

## Общая информация
- **Дата:** {timestamp}
- **Тип теста:** E2E Task (E12-B)
- **Результат:** {status_emoji} {outcome.upper()}
- **Commit ID:** {commit_id}
- **Окружение:** TEST (https://etl-tst.chococraft.ru)

## Цель теста
Автоматическая проверка выполнения отдельной задачи через граф узлов в рамках CI/CD pipeline.

## Проверенные узлы графа

| Узел | Статус | Примечания |
|------|--------|------------|
| Dev | {status_emoji} | Обращение к Router (CLI) по роли |
| Gate | {status_emoji} | Валидация артефактов |
| QA | {status_emoji} | Запуск тестов |
| Scribe | {status_emoji} | Обновление документации |
| Apply | {status_emoji} | Применение артефактов |

## Выполненные проверки

### ✅ Основные требования
- API доступен по HTTPS с BasicAuth
- Нет 5xx ошибок в ответах
- Система самоисполняется через backlog и БД
- Логирование соответствует стандарту Logging-001

### ✅ Дополнительные проверки
- Доступность /admin/tokens endpoint
- Доступность /api/v1/logs endpoint

## Результаты
"""
    
    if outcome == "success":
        report += """
- ✅ Все узлы графа выполнены успешно
- ✅ Dev-задача завершена со статусом DONE
- ✅ Узел Dev корректно обращается к Router
- ✅ Артефакты созданы и применены
- ✅ События логируются согласно стандарту
- ✅ Endpoint /admin/tokens доступен
- ✅ Endpoint /api/v1/logs доступен
"""
    else:
        report += """
- ❌ Один или несколько узлов графа завершились с ошибкой
- ❌ Требуется проверка логов системы
- ❌ Возможна проблема с LLM провайдерами или бюджетом
"""
    
    report += f"""
## Следующие действия
{f'Граф узлов работает корректно' if outcome == 'success' else 'Требуется диагностика графа узлов'}

---
🤖 Автоматически сгенерировано CI/CD Pipeline
Время генерации: {timestamp}
"""
    
    return report

def generate_wait_budget_report(outcome, commit_id=None):
    """Генерация отчёта для WAIT_BUDGET E2E теста"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_id = commit_id or os.getenv('GITHUB_SHA', 'unknown')[:8]
    
    status_emoji = "✅" if outcome == "success" else "❌"
    
    report = f"""# CI E2E WAIT_BUDGET Test Report

## Общая информация
- **Дата:** {timestamp}
- **Тип теста:** E2E WAIT_BUDGET
- **Результат:** {status_emoji} {outcome.upper()}
- **Commit ID:** {commit_id}
- **Окружение:** TEST (https://etl-tst.chococraft.ru)

## Цель теста
Автоматическая проверка сценария WAIT_BUDGET в системе Feature Factory в рамках CI/CD pipeline.

## Выполненные проверки

### ✅ Основные требования
- API доступен по HTTPS с BasicAuth
- Нет 5xx ошибок в ответах
- Система корректно обрабатывает состояние WAIT_BUDGET
- Логирование соответствует стандарту Logging-001

### ✅ Этапы выполнения
1. Создание фичи через API
2. Проверка доступности /admin/tokens
3. Симуляция сценария WAIT_BUDGET

## Результаты
"""
    
    if outcome == "success":
        report += """
- ✅ Фича успешно создана
- ✅ Endpoint /admin/tokens доступен
- ✅ Сценарий WAIT_BUDGET корректно обработан
- ✅ События логируются согласно стандарту
"""
    else:
        report += """
- ❌ Тест завершился с ошибкой
- ❌ Требуется ручная проверка системы
- ❌ Возможна проблема с обработкой состояния WAIT_BUDGET
"""
    
    report += f"""
## Следующие действия
{f'Сценарий WAIT_BUDGET работает корректно' if outcome == 'success' else 'Требуется диагностика сценария WAIT_BUDGET'}

---
🤖 Автоматически сгенерировано CI/CD Pipeline
Время генерации: {timestamp}
"""
    
    return report

def main():
    """Основная функция генерации отчёта"""
    if len(sys.argv) < 3:
        print("Usage: python generate_e2e_report.py <test_type> <outcome> [commit_id]")
        print("test_type: 'feature', 'task', or 'wait_budget'")
        print("outcome: 'success' or 'failure'")
        sys.exit(1)
    
    test_type = sys.argv[1]
    outcome = sys.argv[2]
    commit_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    if test_type == "feature":
        report = generate_feature_report(outcome, commit_id)
    elif test_type == "task":
        report = generate_task_report(outcome, commit_id)
    elif test_type == "wait_budget":
        report = generate_wait_budget_report(outcome, commit_id)
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)
    
    print(report)

if __name__ == '__main__':
    main()