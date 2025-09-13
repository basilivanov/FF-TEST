#!/usr/bin/env python3
"""
Тестирование ContextPackager для роли Dev с реальной задачей
"""
import sys
import os
import json
from datetime import datetime
sys.path.append('/opt/feature-factory')

from app.context.packager import ContextPackager

def load_test_task():
    """Загружает тестовое задание"""
    try:
        with open('/opt/feature-factory/artifacts/CTX_WIRING/CTX_WIRE_20250913_174028/dev_test_task.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки задания: {e}")
        return None

def run_context_packager_test():
    """Запускает тест ContextPackager для роли Dev"""
    
    print("=== Тестирование ContextPackager для роли Dev ===")
    
    # Загружаем задание
    task_data = load_test_task()
    if not task_data:
        return None
        
    # Создаем экземпляр ContextPackager
    try:
        packager = ContextPackager()
    except Exception as e:
        print(f"Ошибка создания ContextPackager: {e}")
        return None
    
    # Формируем задачу в формате ContextPackager
    task = {
        "correlation_id": task_data["correlation_id"],
        "title": task_data["task_title"],
        "role": task_data["role"],
        "user_intent": task_data["user_intent"],
        "description": task_data["task_description"],
        "expected_files": task_data.get("expected_files", []),
        "constraints": task_data.get("constraints", [])
    }
    
    print(f"Задача: {task['title']}")
    print(f"Роль: {task['role']}")
    print(f"Correlation ID: {task['correlation_id']}")
    
    # Запускаем build_context_for_task
    try:
        print("\\nЗапуск ContextPackager.build_context_for_task()...")
        context_md = packager.build_context_for_task(task)
        
        if context_md.startswith('{"error":'):
            # NeedContext ошибка
            error_data = json.loads(context_md)
            print(f"\\n❌ NeedContext Error: {error_data}")
            return {
                "status": "need_context_error",
                "error": error_data,
                "context_length": 0,
                "analysis": "ContextPackager вернул NeedContext - недостаточно контекста для роли Dev"
            }
        
        # Успешно получен контекст
        context_length = len(context_md)
        print(f"\\n✅ Контекст успешно сгенерирован")
        print(f"Размер контекста: {context_length} символов")
        
        # Сохраняем полный контекст в файл
        context_file = f"/opt/feature-factory/artifacts/CTX_WIRING/CTX_WIRE_20250913_174028/dev_context_full.md"
        with open(context_file, 'w') as f:
            f.write(context_md)
        print(f"Полный контекст сохранен в: {context_file}")
        
        return {
            "status": "success",
            "context_md": context_md,
            "context_length": context_length,
            "context_file": context_file,
            "task": task
        }
        
    except Exception as e:
        print(f"\\n❌ Ошибка выполнения: {e}")
        return {
            "status": "execution_error", 
            "error": str(e),
            "context_length": 0
        }

def analyze_context_quality(result):
    """Анализирует качество сгенерированного контекста"""
    
    if result["status"] != "success":
        return {
            "quality_score": 0,
            "issues": [f"Контекст не сгенерирован: {result.get('error', 'unknown')}"],
            "recommendations": ["Исправить ошибки ContextPackager"]
        }
    
    context_md = result["context_md"]
    task = result["task"]
    
    analysis = {
        "quality_score": 0,
        "sections_found": [],
        "missing_sections": [],
        "file_coverage": {},
        "api_coverage": {},
        "issues": [],
        "strengths": [],
        "recommendations": []
    }
    
    # Проверяем наличие ключевых секций
    expected_sections = [
        "# Контекст задачи",
        "## Репозиторий",
        "## Файловая структура", 
        "## API спецификации",
        "## Политики безопасности",
        "## Директивы кодирования"
    ]
    
    for section in expected_sections:
        if section in context_md:
            analysis["sections_found"].append(section)
            analysis["quality_score"] += 10
        else:
            analysis["missing_sections"].append(section)
    
    # Проверяем покрытие файлов
    expected_files = task.get("expected_files", [])
    for file_path in expected_files:
        if file_path in context_md:
            analysis["file_coverage"][file_path] = "found"
        else:
            analysis["file_coverage"][file_path] = "missing"
            analysis["issues"].append(f"Отсутствует информация о файле: {file_path}")
    
    # Проверяем API информацию
    api_keywords = ["FastAPI", "Pydantic", "SQLAlchemy", "endpoint", "schema"]
    api_found = 0
    for keyword in api_keywords:
        if keyword.lower() in context_md.lower():
            api_found += 1
            analysis["api_coverage"][keyword] = "found"
        else:
            analysis["api_coverage"][keyword] = "missing"
    
    analysis["quality_score"] += api_found * 5
    
    # Проверяем размер контекста
    context_length = result["context_length"]
    if context_length > 5000:
        analysis["strengths"].append(f"Достаточный размер контекста: {context_length} символов")
        analysis["quality_score"] += 15
    elif context_length > 2000:
        analysis["quality_score"] += 10
    else:
        analysis["issues"].append(f"Слишком малый размер контекста: {context_length} символов")
    
    # Формируем рекомендации
    if len(analysis["missing_sections"]) > 0:
        analysis["recommendations"].append("Добавить недостающие секции контекста")
    
    if len([f for f in analysis["file_coverage"].values() if f == "missing"]) > 0:
        analysis["recommendations"].append("Улучшить покрытие файлов в контексте")
    
    if api_found < 3:
        analysis["recommendations"].append("Добавить больше API/технической документации")
    
    return analysis

def generate_report(test_result, quality_analysis):
    """Генерирует итоговый отчет"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Отчет тестирования ContextPackager для роли Dev

**Дата**: {timestamp}  
**Correlation ID**: {test_result.get('task', {}).get('correlation_id', 'N/A')}  
**Статус**: {test_result['status']}

## Обзор задания

**Задача**: {test_result.get('task', {}).get('title', 'N/A')}  
**Роль**: Dev  
**Описание**: Создание CRUD endpoint для управления пользователями

## Результаты тестирования

### Статус выполнения ContextPackager
- **Результат**: {'✅ Успешно' if test_result['status'] == 'success' else '❌ Ошибка'}
- **Размер контекста**: {test_result['context_length']} символов
- **Файл контекста**: {test_result.get('context_file', 'N/A')}

### Анализ качества контекста

**Оценка качества**: {quality_analysis['quality_score']}/100

#### Найденные секции ({len(quality_analysis['sections_found'])})
"""
    
    for section in quality_analysis['sections_found']:
        report += f"- ✅ {section}\\n"
    
    if quality_analysis['missing_sections']:
        report += f"\\n#### Отсутствующие секции ({len(quality_analysis['missing_sections'])})\\n"
        for section in quality_analysis['missing_sections']:
            report += f"- ❌ {section}\\n"
    
    report += f"\\n#### Покрытие файлов\\n"
    for file_path, status in quality_analysis['file_coverage'].items():
        icon = "✅" if status == "found" else "❌"
        report += f"- {icon} {file_path}: {status}\\n"
    
    report += f"\\n#### API/Техническое покрытие\\n"
    for keyword, status in quality_analysis['api_coverage'].items():
        icon = "✅" if status == "found" else "❌"
        report += f"- {icon} {keyword}: {status}\\n"
    
    if quality_analysis['strengths']:
        report += f"\\n### ✅ Сильные стороны\\n"
        for strength in quality_analysis['strengths']:
            report += f"- {strength}\\n"
    
    if quality_analysis['issues']:
        report += f"\\n### ❌ Проблемы\\n"
        for issue in quality_analysis['issues']:
            report += f"- {issue}\\n"
    
    if quality_analysis['recommendations']:
        report += f"\\n### 💡 Рекомендации\\n"
        for rec in quality_analysis['recommendations']:
            report += f"- {rec}\\n"
    
    # Итоговая оценка
    score = quality_analysis['quality_score']
    if score >= 80:
        verdict = "🟢 ОТЛИЧНО - Контекст полный и подходит для работы Dev роли"
    elif score >= 60:
        verdict = "🟡 ХОРОШО - Контекст достаточен, но есть области для улучшения"
    elif score >= 40:
        verdict = "🟠 УДОВЛЕТВОРИТЕЛЬНО - Контекст частично полезен, нужны улучшения"
    else:
        verdict = "🔴 ПЛОХО - Контекст недостаточен для эффективной работы"
    
    report += f"\\n## Итоговая оценка\\n\\n{verdict}\\n"
    report += f"\\n**Оценка**: {score}/100 баллов\\n"
    
    return report

if __name__ == "__main__":
    # Запускаем тест
    result = run_context_packager_test()
    if not result:
        print("❌ Не удалось выполнить тест")
        exit(1)
    
    # Анализируем качество
    analysis = analyze_context_quality(result)
    
    # Генерируем отчет
    report = generate_report(result, analysis)
    
    # Сохраняем отчет
    report_file = "/opt/feature-factory/artifacts/CTX_WIRING/CTX_WIRE_20250913_174028/dev_context_analysis_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\\n📊 Отчет сохранен в: {report_file}")
    print(f"\\n🎯 Итоговая оценка: {analysis['quality_score']}/100")