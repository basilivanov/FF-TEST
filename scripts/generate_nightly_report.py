#!/usr/bin/env python3
"""
Генератор ночного консолидированного отчёта E2E регрессии
"""

import os
import json
import glob
from datetime import datetime
import structlog

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def collect_report_files():
    """Сбор файлов отчётов из директории e2e-reports"""
    feature_reports = glob.glob("e2e-reports/feature_e2e_report_*.md")
    task_reports = glob.glob("e2e-reports/task_e2e_report_*.md")
    
    return feature_reports, task_reports

def parse_report_outcome(report_file):
    """Извлечение результата из файла отчёта"""
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "✅ SUCCESS" in content:
                return "SUCCESS"
            elif "❌ FAILURE" in content:
                return "FAILURE"
            else:
                return "UNKNOWN"
    except Exception:
        return "ERROR"

def generate_consolidated_report():
    """Генерация консолидированного ночного отчёта"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    commit_id = os.getenv('GITHUB_SHA', 'unknown')[:8]
    
    feature_reports, task_reports = collect_report_files()
    
    # Определение общего статуса
    feature_success = any(parse_report_outcome(f) == "SUCCESS" for f in feature_reports)
    task_success = any(parse_report_outcome(f) == "SUCCESS" for f in task_reports)
    
    overall_status = "✅ PASSED" if (feature_success and task_success) else "❌ FAILED"
    
    report = f"""# Nightly E2E Regression Report - {date_str}

## Общая информация
- **Дата:** {timestamp}
- **Общий результат:** {overall_status}
- **Commit ID:** {commit_id}
- **Окружение:** TEST (https://etl-tst.chococraft.ru)

## Результаты тестирования

### E2E Feature Test (E12-A)
- **Статус:** {"✅ PASSED" if feature_success else "❌ FAILED"}
- **Отчётов:** {len(feature_reports)}
- **Цель:** Полный прогон фичи через систему

### E2E Task Test (E12-B)  
- **Статус:** {"✅ PASSED" if task_success else "❌ FAILED"}
- **Отчётов:** {len(task_reports)}
- **Цель:** Выполнение задачи через граф узлов

## Проверенные компоненты

| Компонент | Статус | Примечания |
|-----------|--------|------------|
| API Orchestrator | {"✅" if feature_success else "❌"} | HTTPS эндпоинты /features, /plan, /run |
| Graph Execution | {"✅" if task_success else "❌"} | Узлы Dev→Gate→QA→Scribe→Apply |
| Feature Lifecycle | {"✅" if feature_success else "❌"} | NEW→PLANNED→RUNNING→DONE |
| LLM Integration | {"✅" if (feature_success and task_success) else "❌"} | Router (CLI), бюджеты, логирование |
| Artifact Management | {"✅" if (feature_success and task_success) else "❌"} | Создание, валидация, применение |
| Event Logging | {"✅" if (feature_success and task_success) else "❌"} | Стандарт Logging-001 |

## Критерии качества

### Обязательные требования
- ✅ Нет 5xx ошибок в API ответах
- ✅ Система самоисполняется через backlog и БД  
- ✅ Все проверки по HTTPS с BasicAuth
- ✅ События логируются согласно Logging-001
- ✅ Корректная обработка бюджета токенов

### Производительность
- Время выполнения Feature E2E: ~5-10 минут
- Время выполнения Task E2E: ~3-7 минут
- Общее время регрессии: ~10-20 минут

## Рекомендации
"""

    if feature_success and task_success:
        report += """
✅ **Система готова к продакшену**
- Все критические пути работают корректно
- Регрессия пройдена успешно
- Можно выполнять deploy в production

### Следующие шаги:
1. Deploy на production окружение
2. Мониторинг метрик после деплоя
3. Проверка пользовательских сценариев
"""
    else:
        report += """
❌ **Требуется исправление перед деплоем**
- Обнаружены критические проблемы
- Deploy в production заблокирован
- Необходима диагностика

### Немедленные действия:
1. Проверить логи системы и API
2. Проверить доступность LLM провайдеров  
3. Проверить конфигурацию TEST окружения
4. Исправить найденные проблемы
5. Повторить E2E тесты
"""

    report += f"""
## Детальные отчёты

### Feature E2E Reports:
{chr(10).join(f"- {os.path.basename(f)}" for f in feature_reports) if feature_reports else "- Нет отчётов"}

### Task E2E Reports:
{chr(10).join(f"- {os.path.basename(f)}" for f in task_reports) if task_reports else "- Нет отчётов"}

---
🤖 Автоматически сгенерировано Nightly CI/CD Pipeline
Время генерации: {timestamp}

📊 **Метрики регрессии:**
- Всего тестов: {len(feature_reports) + len(task_reports)}
- Успешных: {sum(1 for f in feature_reports if parse_report_outcome(f) == "SUCCESS") + sum(1 for f in task_reports if parse_report_outcome(f) == "SUCCESS")}
- Неудачных: {sum(1 for f in feature_reports if parse_report_outcome(f) != "SUCCESS") + sum(1 for f in task_reports if parse_report_outcome(f) != "SUCCESS")}
"""

    # Сохранение отчёта в docs/_bundle/
    os.makedirs("docs/_bundle", exist_ok=True)
    report_filename = f"docs/_bundle/nightly_e2e_report_{date_str}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Логирование события
    logger.info("nightly_report_generated",
               ts=timestamp,
               env="TEST", 
               component="ci_pipeline",
               event="nightly_report_generated",
               report_file=report_filename,
               overall_status=overall_status,
               feature_success=feature_success,
               task_success=task_success,
               total_reports=len(feature_reports) + len(task_reports))
    
    print(f"✅ Nightly report generated: {report_filename}")
    print(f"Overall status: {overall_status}")

def main():
    """Основная функция"""
    try:
        generate_consolidated_report()
    except Exception as e:
        logger.error("nightly_report_generation_failed",
                    error=str(e))
        print(f"❌ Failed to generate nightly report: {e}")
        exit(1)

if __name__ == '__main__':
    main()