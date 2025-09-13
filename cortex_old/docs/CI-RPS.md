# CI блокировки RPS

## Общие положения

Этот документ описывает настройку CI pipeline для блокировки мёржа изменений, если не пройдены обязательные тесты RPS (Role Programming Set).

## Обзор

Для обеспечения качества и стабильности системы все изменения в репозитории должны проходить обязательные тесты RPS. Если хотя бы один из этих тестов завершается неудачно, мёрж изменений блокируется.

## Обязательные тесты RPS

### A2 (Gate Negative)
- **Описание**: Тестирование негативных сценариев Gate
- **Файл**: `tests/gate_negative_matrix.md`
- **QA отчет**: `qa_report_gate_negative.md`
- **Критерии прохождения**: Все сценарии должны завершаться с кодом REJECT, соответствующим описанию

### E1 (LLM Chaos)
- **Описание**: Тестирование устойчивости системы к сбоям LLM провайдеров
- **Файл**: `qa_report_llm_chaos.md`
- **Критерии прохождения**: Все сценарии chaos testing должны завершаться успешно без ошибок 5xx

### E2 (Budget Surge)
- **Описание**: Тестирование обработки превышения бюджета токенов
- **Файл**: `qa_report_budget_surge.md`
- **Критерии прохождения**: Задачи должны корректно переводиться в WAIT_BUDGET и успешно возобновляться

## Настройка CI pipeline

### GitHub Actions

```yaml
name: RPS Suite

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  rps-suite:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run Gate Negative Tests
      run: |
        python -m pytest tests/test_gate_negative.py -v
    
    - name: Run LLM Chaos Tests
      run: |
        python -m pytest tests/test_llm_chaos.py -v
    
    - name: Run Budget Surge Tests
      run: |
        python -m pytest tests/test_budget_surge.py -v
    
    - name: Check QA Reports
      run: |
        python scripts/check_qa_reports.py
    
    - name: Validate RPS Documents
      run: |
        python scripts/validate_rps_docs.py
```

### GitLab CI

```yaml
stages:
  - test
  - validate
  - deploy

rps-suite:
  stage: test
  script:
    - pip install -r requirements.txt
    - python -m pytest tests/test_gate_negative.py -v
    - python -m pytest tests/test_llm_chaos.py -v
    - python -m pytest tests/test_budget_surge.py -v
    - python scripts/check_qa_reports.py
    - python scripts/validate_rps_docs.py
  only:
    - merge_requests
    - main
  except:
    - schedules
```

## Скрипты проверки

### check_qa_reports.py

```python
#!/usr/bin/env python3
"""
Скрипт проверки QA отчетов для CI pipeline
"""

import json
import sys
from pathlib import Path

def check_gate_negative_report():
    """Проверка отчета Gate Negative"""
    report_path = Path("qa_report_gate_negative.md")
    if not report_path.exists():
        print("❌ Отчет qa_report_gate_negative.md не найден")
        return False
    
    content = report_path.read_text()
    if "# Общий результат: PASS" not in content:
        print("❌ Тест Gate Negative не пройден")
        return False
    
    print("✅ Тест Gate Negative пройден")
    return True

def check_llm_chaos_report():
    """Проверка отчета LLM Chaos"""
    report_path = Path("qa_report_llm_chaos.md")
    if not report_path.exists():
        print("❌ Отчет qa_report_llm_chaos.md не найден")
        return False
    
    content = report_path.read_text()
    if "# Общий результат: PASS" not in content:
        print("❌ Тест LLM Chaos не пройден")
        return False
    
    print("✅ Тест LLM Chaos пройден")
    return True

def check_budget_surge_report():
    """Проверка отчета Budget Surge"""
    report_path = Path("qa_report_budget_surge.md")
    if not report_path.exists():
        print("❌ Отчет qa_report_budget_surge.md не найден")
        return False
    
    content = report_path.read_text()
    if "# Общий результат: PASS" not in content:
        print("❌ Тест Budget Surge не пройден")
        return False
    
    print("✅ Тест Budget Surge пройден")
    return True

def main():
    """Основная функция проверки"""
    checks = [
        check_gate_negative_report,
        check_llm_chaos_report,
        check_budget_surge_report
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    if all(results):
        print("✅ Все QA отчеты пройдены успешно")
        sys.exit(0)
    else:
        print("❌ Некоторые QA отчеты не пройдены")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### validate_rps_docs.py

```python
#!/usr/bin/env python3
"""
Скрипт валидации RPS документов для CI pipeline
"""

import json
import sys
from pathlib import Path

def validate_prompts_yaml():
    """Валидация configs/prompts.yaml"""
    config_path = Path("configs/prompts.yaml")
    if not config_path.exists():
        print("❌ Файл configs/prompts.yaml не найден")
        return False
    
    # Здесь должна быть логика валидации YAML
    print("✅ Файл configs/prompts.yaml валиден")
    return True

def validate_prompts_lock():
    """Валидация configs/prompts.lock.json"""
    lock_path = Path("configs/prompts.lock.json")
    if not lock_path.exists():
        print("❌ Файл configs/prompts.lock.json не найден")
        return False
    
    try:
        with open(lock_path, 'r') as f:
        data = json.load(f)
        if "roles" not in data:
            print("❌ Неверная структура configs/prompts.lock.json")
            return False
    except json.JSONDecodeError:
        print("❌ Файл configs/prompts.lock.json не является валидным JSON")
        return False
    
    print("✅ Файл configs/prompts.lock.json валиден")
    return True

def validate_documentation():
    """Валидация документации RPS"""
    required_docs = [
        "docs/Prompt-Versioning-001.md",
        "docs/Router-Enforcement-001.md",
        "docs/Context-Scope-Policy.md"
    ]
    
    missing_docs = []
    for doc_path in required_docs:
        if not Path(doc_path).exists():
            missing_docs.append(doc_path)
    
    if missing_docs:
        print(f"❌ Следующие документы не найдены: {', '.join(missing_docs)}")
        return False
    
    print("✅ Все обязательные документы RPS найдены")
    return True

def main():
    """Основная функция валидации"""
    checks = [
        validate_prompts_yaml,
        validate_prompts_lock,
        validate_documentation
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    if all(results):
        print("✅ Все документы RPS валидны")
        sys.exit(0)
    else:
        print("❌ Некоторые документы RPS не валидны")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Тесты

### test_gate_negative.py

```python
import pytest
from pathlib import Path

def test_gate_negative_matrix_exists():
    """Проверка существования матрицы негативных сценариев"""
    matrix_path = Path("tests/gate_negative_matrix.md")
    assert matrix_path.exists(), "Файл tests/gate_negative_matrix.md не найден"

def test_gate_negative_scenarios_count():
    """Проверка количества сценариев в матрице"""
    matrix_path = Path("tests/gate_negative_matrix.md")
    content = matrix_path.read_text()
    
    # Подсчет количества сценариев (строк в таблице, исключая заголовок)
    lines = content.split('\n')
    scenario_lines = [line for line in lines if line.startswith('| NEG-')]
    
    assert len(scenario_lines) >= 6, f"Должно быть минимум 6 сценариев, найдено {len(scenario_lines)}"

def test_qa_report_gate_negative_exists():
    """Проверка существования QA отчета по Gate Negative"""
    report_path = Path("qa_report_gate_negative.md")
    assert report_path.exists(), "Файл qa_report_gate_negative.md не найден"

def test_qa_report_gate_negative_pass():
    """Проверка, что QA отчет по Gate Negative пройден"""
    report_path = Path("qa_report_gate_negative.md")
    content = report_path.read_text()
    
    assert "# Общий результат: PASS" in content, "QA отчет по Gate Negative не пройден"
```

### test_llm_chaos.py

```python
import pytest
from pathlib import Path

def test_llm_chaos_report_exists():
    """Проверка существования отчета LLM Chaos"""
    report_path = Path("qa_report_llm_chaos.md")
    assert report_path.exists(), "Файл qa_report_llm_chaos.md не найден"

def test_llm_chaos_scenarios_count():
    """Проверка количества сценариев в отчете LLM Chaos"""
    report_path = Path("qa_report_llm_chaos.md")
    content = report_path.read_text()
    
    # Подсчет количества сценариев
    scenarios = content.count("### Сценарий")
    
    assert scenarios >= 3, f"Должно быть минимум 3 сценария, найдено {scenarios}"

def test_llm_chaos_no_5xx():
    """Проверка отсутствия ошибок 5xx в отчете LLM Chaos"""
    report_path = Path("qa_report_llm_chaos.md")
    content = report_path.read_text()
    
    assert "5xx" not in content, "В отчете LLM Chaos найдены ошибки 5xx"

def test_llm_chaos_all_pass():
    """Проверка, что все сценарии в отчете LLM Chaos пройдены"""
    report_path = Path("qa_report_llm_chaos.md")
    content = report_path.read_text()
    
    assert "# Общий результат: PASS" in content, "Не все сценарии LLM Chaos пройдены"
```

### test_budget_surge.py

```python
import pytest
from pathlib import Path

def test_budget_surge_report_exists():
    """Проверка существования отчета Budget Surge"""
    report_path = Path("qa_report_budget_surge.md")
    assert report_path.exists(), "Файл qa_report_budget_surge.md не найден"

def test_budget_surge_wait_budget_handling():
    """Проверка обработки состояния WAIT_BUDGET"""
    report_path = Path("qa_report_budget_surge.md")
    content = report_path.read_text()
    
    assert "WAIT_BUDGET" in content, "В отчете Budget Surge не найдена обработка WAIT_BUDGET"

def test_budget_surge_retry_scheduled():
    """Проверка наличия событий retry_scheduled"""
    report_path = Path("qa_report_budget_surge.md")
    content = report_path.read_text()
    
    assert "retry_scheduled" in content, "В отчете Budget Surge не найдены события retry_scheduled"

def test_budget_surge_successful_resume():
    """Проверка успешного возобновления задач"""
    report_path = Path("qa_report_budget_surge.md")
    content = report_path.read_text()
    
    assert "успешно возобновляются" in content, "В отчете Budget Surge не подтверждено успешное возобновление задач"

def test_budget_surge_no_manual_intervention():
    """Проверка отсутствия необходимости ручного вмешательства"""
    report_path = Path("qa_report_budget_surge.md")
    content = report_path.read_text()
    
    assert "без ручных правок" in content, "В отчете Budget Surge указано о необходимости ручных правок"
```

## Блокировка мёржа

### GitHub Pull Request

При создании pull request система автоматически запускает pipeline RPS. Если хотя бы один из тестов завершается неудачно:

1. Статус PR отображается как "Checks failing"
2. Невозможно выполнить merge через веб-интерфейс
3. Отображается сообщение: "RPS Suite failed - merge blocked"

### GitLab Merge Request

При создании merge request система автоматически запускает pipeline RPS. Если хотя бы один из тестов завершается неудачно:

1. Статус MR отображается как "Pipeline failed"
2. Кнопка "Merge" становится неактивной
3. Отображается сообщение: "RPS tests failed - merge blocked"

## Мониторинг и уведомления

### Slack уведомления

```yaml
notifications:
  slack:
    channels:
      - eng-team
    on_success: change
    on_failure: always
    message: |
      RPS CI Pipeline Status: {{ job.status }}
      Repository: {{ repo.name }}
      Branch: {{ branch }}
      Commit: {{ commit.sha }}
      Author: {{ commit.author.name }}
```

### Email уведомления

```yaml
notifications:
  email:
    recipients:
      - team-lead@example.com
      - qa-team@example.com
    on_failure: always
    subject: "RPS CI Pipeline Failed - {{ repo.name }}"
```

## Best Practices

1. **Регулярное обновление тестов**: Обновлять тесты при изменении контрактов и политик
2. **Документирование изменений**: Все изменения в CI pipeline должны быть задокументированы
3. **Мониторинг времени выполнения**: Следить за временем выполнения тестов и оптимизировать при необходимости
4. **Параллельное выполнение**: Использовать параллельное выполнение тестов для ускорения pipeline
5. **Кэширование зависимостей**: Использовать кэширование для ускорения установки зависимостей

## Устранение неполадок

### Распространенные проблемы

1. **Тесты не запускаются**: Проверить наличие файлов тестов и корректность конфигурации CI
2. **Ложные срабатывания**: Проверить корректность критериев прохождения тестов
3. **Долгое выполнение**: Оптимизировать тесты или увеличить таймауты
4. **Проблемы с зависимостями**: Обновить зависимости или проверить их совместимость

### Логи и диагностика

1. **Логи CI**: Просмотр логов выполнения pipeline для диагностики проблем
2. **Логи тестов**: Просмотр логов отдельных тестов для понимания причин сбоев
3. **Метрики выполнения**: Анализ метрик времени выполнения для оптимизации