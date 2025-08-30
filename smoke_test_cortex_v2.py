#!/usr/bin/env python3
"""
Smoke Test для Cortex v2 - расширенного "Кортекса" с "Хранилищем" и "Доктриной"

Тестирует:
1. Структуру файлов Cortex v2
2. Доступность и содержимое файлов доктрины и карты секретов
3. Логику ContextPackager для автоматического включения доктрины и секретов
4. Детектирование ключевых слов безопасности
5. Формирование полного контекста
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append('/opt/feature-factory')

from app.context.packager import ContextPackager


def test_file_structure() -> Dict[str, Any]:
    """Проверяет структуру файлов Cortex v2"""
    print("📁 Тестирование структуры файлов...")
    
    results = {
        "test_name": "file_structure",
        "status": "success",
        "details": {},
        "errors": []
    }
    
    expected_files = {
        "/opt/feature-factory/cortex/security/credentials.md": "Карта секретов",
        "/opt/feature-factory/cortex/doctrine/common_rules.md": "Правила и анти-паттерны"
    }
    
    for filepath, description in expected_files.items():
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    results["details"][description] = {
                        "exists": True,
                        "size": len(content),
                        "lines": len(content.split('\n'))
                    }
                    print(f"  ✅ {description}: {len(content)} символов, {len(content.split('\n'))} строк")
            except Exception as e:
                results["errors"].append(f"Ошибка чтения {filepath}: {e}")
                results["status"] = "error"
        else:
            results["errors"].append(f"Файл не найден: {filepath}")
            results["status"] = "error"
    
    return results


def test_doctrine_content() -> Dict[str, Any]:
    """Проверяет содержимое доктрины"""
    print("\n📜 Тестирование содержимого доктрины...")
    
    results = {
        "test_name": "doctrine_content",
        "status": "success",
        "details": {},
        "errors": []
    }
    
    try:
        with open("/opt/feature-factory/cortex/doctrine/common_rules.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем ключевые секции
        expected_sections = [
            "КРИТИЧЕСКИЕ ЗАПРЕТЫ",
            "ЗАПРЕЩЕНО",
            "ПРАВИЛЬНО",
            "IndentationError",
            "uvicorn", 
            "Alembic",
            "secret_store"
        ]
        
        found_sections = []
        missing_sections = []
        
        for section in expected_sections:
            if section in content:
                found_sections.append(section)
                print(f"  ✅ Найдена секция: {section}")
            else:
                missing_sections.append(section)
                print(f"  ❌ Отсутствует секция: {section}")
        
        results["details"]["found_sections"] = found_sections
        results["details"]["missing_sections"] = missing_sections
        results["details"]["total_sections"] = len(expected_sections)
        results["details"]["found_count"] = len(found_sections)
        
        if missing_sections:
            results["status"] = "warning"
            results["errors"].append(f"Отсутствуют секции: {missing_sections}")
            
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Ошибка анализа доктрины: {e}")
    
    return results


def test_credentials_content() -> Dict[str, Any]:
    """Проверяет содержимое карты секретов"""
    print("\n🔐 Тестирование карты секретов...")
    
    results = {
        "test_name": "credentials_content", 
        "status": "success",
        "details": {},
        "errors": []
    }
    
    try:
        with open("/opt/feature-factory/cortex/security/credentials.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем ключевые элементы
        expected_elements = [
            "secret_store.get_secret",
            "admin.ui.username",
            "admin.ui.password", 
            "database.url",
            "НИКОГДА",
            "hardcoded_password",
            "from app.api.secrets import secret_store"
        ]
        
        found_elements = []
        missing_elements = []
        
        for element in expected_elements:
            if element in content:
                found_elements.append(element)
                print(f"  ✅ Найден элемент: {element}")
            else:
                missing_elements.append(element)
                print(f"  ❌ Отсутствует элемент: {element}")
        
        # Проверяем, что нет хардкода секретов
        dangerous_patterns = ["password123", "admin123", "secret123", "key123"]
        found_dangerous = [p for p in dangerous_patterns if p in content]
        
        results["details"]["found_elements"] = found_elements
        results["details"]["missing_elements"] = missing_elements
        results["details"]["dangerous_patterns"] = found_dangerous
        results["details"]["elements_coverage"] = len(found_elements) / len(expected_elements)
        
        if missing_elements:
            results["status"] = "warning"
            results["errors"].append(f"Отсутствуют элементы: {missing_elements}")
            
        if found_dangerous:
            results["status"] = "error"
            results["errors"].append(f"Найдены потенциально опасные паттерны: {found_dangerous}")
            
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Ошибка анализа карты секретов: {e}")
    
    return results


def test_packager_basic() -> Dict[str, Any]:
    """Тестирует базовую логику ContextPackager"""
    print("\n🤖 Тестирование базовой логики ContextPackager...")
    
    results = {
        "test_name": "packager_basic",
        "status": "success", 
        "details": {},
        "errors": []
    }
    
    try:
        packager = ContextPackager()
        
        # Тест 1: Обычная задача без секретов
        basic_task = {
            'id': 1,
            'feature_id': 'test-basic',
            'role': 'Dev',
            'dsl_json': json.dumps({
                'description': 'Создать новую функцию обработки данных',
                'name': 'process_data'
            })
        }
        
        context = packager.build_context_for_task(basic_task)
        
        has_doctrine = "# ДОКТРИНА И ПРАВИЛА РАБОТЫ" in context
        has_security = "# КАРТА ДОСТУПА К СЕКРЕТАМ" in context
        
        results["details"]["basic_task"] = {
            "context_length": len(context),
            "has_doctrine": has_doctrine,
            "has_security": has_security,
            "expected_security": False
        }
        
        print(f"  ✅ Базовая задача: {len(context)} символов")
        print(f"  ✅ Содержит доктрину: {has_doctrine}")
        print(f"  ✅ НЕ содержит секреты: {not has_security} (ожидалось)")
        
        if not has_doctrine:
            results["status"] = "error"
            results["errors"].append("Доктрина не добавилась в базовую задачу")
            
        if has_security:
            results["status"] = "warning"
            results["errors"].append("Секреты неожиданно добавились в базовую задачу")
            
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Ошибка тестирования базовой логики: {e}")
    
    return results


def test_packager_security_detection() -> Dict[str, Any]:
    """Тестирует детектирование ключевых слов безопасности"""
    print("\n🔍 Тестирование детектирования безопасности...")
    
    results = {
        "test_name": "security_detection",
        "status": "success",
        "details": {},
        "errors": []
    }
    
    try:
        packager = ContextPackager()
        
        # Тесты с разными ключевыми словами
        test_cases = [
            {
                "name": "admin_access",
                "description": "Получить доступ к админке",
                "should_trigger": True
            },
            {
                "name": "password_reset", 
                "description": "Сбросить пароль пользователя",
                "should_trigger": True
            },
            {
                "name": "api_key_setup",
                "description": "Настроить API ключи для интеграции",
                "should_trigger": True
            },
            {
                "name": "login_form",
                "description": "Создать форму логина",
                "should_trigger": True
            },
            {
                "name": "regular_task",
                "description": "Создать компонент отображения данных",
                "should_trigger": False
            }
        ]
        
        detection_results = []
        
        for test_case in test_cases:
            task = {
                'id': 1,
                'feature_id': f'test-{test_case["name"]}',
                'role': 'Dev',
                'dsl_json': json.dumps({
                    'description': test_case["description"]
                })
            }
            
            context = packager.build_context_for_task(task)
            has_security = "# КАРТА ДОСТУПА К СЕКРЕТАМ" in context
            
            case_result = {
                "name": test_case["name"],
                "description": test_case["description"],
                "should_trigger": test_case["should_trigger"],
                "actually_triggered": has_security,
                "correct": has_security == test_case["should_trigger"]
            }
            
            detection_results.append(case_result)
            
            status_emoji = "✅" if case_result["correct"] else "❌"
            print(f"  {status_emoji} {test_case['name']}: {case_result['correct']}")
            
        results["details"]["test_cases"] = detection_results
        results["details"]["accuracy"] = sum(1 for r in detection_results if r["correct"]) / len(detection_results)
        
        incorrect_cases = [r for r in detection_results if not r["correct"]]
        if incorrect_cases:
            results["status"] = "error"
            results["errors"].append(f"Неправильно сработали кейсы: {[r['name'] for r in incorrect_cases]}")
            
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Ошибка тестирования детектирования: {e}")
    
    return results


def test_full_context_integration() -> Dict[str, Any]:
    """Тестирует полную интеграцию контекста"""
    print("\n🔄 Тестирование полной интеграции...")
    
    results = {
        "test_name": "full_integration",
        "status": "success",
        "details": {},
        "errors": []
    }
    
    try:
        packager = ContextPackager()
        
        # Комплексная задача с секретами и специфичным контентом
        complex_task = {
            'id': 42,
            'feature_id': 'complex-admin-task',
            'role': 'Dev',
            'dsl_json': json.dumps({
                'name': 'setup_admin_api_auth',
                'description': 'Настроить аутентификацию для admin API с использованием секретных ключей',
                'prompt': 'Нужно получить доступ к базе данных и настроить пароли для админки'
            })
        }
        
        context = packager.build_context_for_task(complex_task)
        
        # Проверяем структуру контекста
        expected_sections = [
            "# ДОКТРИНА И ПРАВИЛА РАБОТЫ",
            "# КАРТА ДОСТУПА К СЕКРЕТАМ", 
            "# Context Package",
            "## Meta",
            "## Task DSL"
        ]
        
        found_sections = []
        section_positions = {}
        
        for section in expected_sections:
            if section in context:
                found_sections.append(section)
                section_positions[section] = context.find(section)
                print(f"  ✅ Найдена секция: {section} (позиция: {section_positions[section]})")
            else:
                print(f"  ❌ Отсутствует секция: {section}")
        
        # Проверяем правильный порядок секций
        positions = list(section_positions.values())
        correct_order = positions == sorted(positions)
        
        results["details"]["context_length"] = len(context)
        results["details"]["found_sections"] = found_sections
        results["details"]["section_positions"] = section_positions
        results["details"]["correct_order"] = correct_order
        results["details"]["sections_coverage"] = len(found_sections) / len(expected_sections)
        
        # Проверяем специфичное содержимое
        key_content_checks = {
            "doctrine_present": "КРИТИЧЕСКИЕ ЗАПРЕТЫ" in context,
            "security_present": "secret_store.get_secret" in context,
            "task_meta_present": '"id": 42' in context,
            "anti_patterns_present": "ЗАПРЕЩЕНО" in context
        }
        
        results["details"]["content_checks"] = key_content_checks
        
        print(f"  ✅ Длина контекста: {len(context)} символов")
        print(f"  ✅ Порядок секций правильный: {correct_order}")
        
        for check_name, passed in key_content_checks.items():
            emoji = "✅" if passed else "❌"
            print(f"  {emoji} {check_name}: {passed}")
            
        # Выявляем проблемы
        if len(found_sections) < len(expected_sections):
            results["status"] = "warning"
            results["errors"].append("Не все ожидаемые секции присутствуют в контексте")
            
        if not correct_order:
            results["status"] = "error"
            results["errors"].append("Нарушен порядок секций в контексте")
            
        if not all(key_content_checks.values()):
            results["status"] = "error"
            failed_checks = [k for k, v in key_content_checks.items() if not v]
            results["errors"].append(f"Не прошли проверки контента: {failed_checks}")
            
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Ошибка интеграционного тестирования: {e}")
    
    return results


def generate_report(test_results: List[Dict[str, Any]]) -> str:
    """Генерирует итоговый отчёт"""
    print("\n📊 Генерация отчёта...")
    
    total_tests = len(test_results)
    success_tests = len([r for r in test_results if r["status"] == "success"])
    warning_tests = len([r for r in test_results if r["status"] == "warning"])
    error_tests = len([r for r in test_results if r["status"] == "error"])
    
    overall_status = "SUCCESS"
    if error_tests > 0:
        overall_status = "ERROR"
    elif warning_tests > 0:
        overall_status = "WARNING"
    
    report = f"""
# Smoke Test Report: Cortex v2 Bootstrap
**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Статус**: {overall_status}

## Сводка результатов
- **Всего тестов**: {total_tests}
- **Успешно**: {success_tests} ✅
- **Предупреждения**: {warning_tests} ⚠️
- **Ошибки**: {error_tests} ❌
- **Процент успеха**: {(success_tests/total_tests)*100:.1f}%

## Детальные результаты

"""
    
    for result in test_results:
        status_emoji = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(result["status"], "❓")
        report += f"### {result['test_name']} {status_emoji}\n"
        report += f"**Статус**: {result['status']}\n\n"
        
        if result["details"]:
            report += "**Детали**:\n"
            for key, value in result["details"].items():
                if isinstance(value, dict):
                    report += f"- {key}:\n"
                    for sub_key, sub_value in value.items():
                        report += f"  - {sub_key}: {sub_value}\n"
                else:
                    report += f"- {key}: {value}\n"
            report += "\n"
        
        if result["errors"]:
            report += "**Ошибки**:\n"
            for error in result["errors"]:
                report += f"- {error}\n"
            report += "\n"
    
    # Рекомендации
    report += "## Рекомендации\n\n"
    
    if overall_status == "SUCCESS":
        report += "🎉 **Все тесты прошли успешно!** Cortex v2 готов к использованию.\n\n"
        report += "### Что работает:\n"
        report += "- ✅ Структура файлов создана корректно\n"
        report += "- ✅ Доктрина содержит все необходимые правила\n"
        report += "- ✅ Карта секретов настроена безопасно\n"
        report += "- ✅ Автоматическое детектирование работает\n"
        report += "- ✅ Интеграция в ContextPackager функциональна\n\n"
    else:
        report += "⚠️ **Обнаружены проблемы, требующие внимания.**\n\n"
        
        if error_tests > 0:
            report += "### Критические проблемы:\n"
            for result in test_results:
                if result["status"] == "error":
                    for error in result["errors"]:
                        report += f"- {error}\n"
            report += "\n"
            
        if warning_tests > 0:
            report += "### Предупреждения:\n"
            for result in test_results:
                if result["status"] == "warning":
                    for error in result["errors"]:
                        report += f"- {error}\n"
            report += "\n"
    
    report += "## Следующие шаги\n\n"
    report += "1. **Тестирование в боевых условиях**: Создать реальную задачу и проверить контекст\n"
    report += "2. **Мониторинг**: Отслеживать логи `context_pack_built` для подтверждения работы\n"
    report += "3. **Обратная связь**: Собирать отзывы агентов о полезности новых секций\n"
    report += "4. **Расширение**: Добавить дополнительные правила по мере выявления паттернов\n\n"
    
    return report


def main():
    """Главная функция smoke test"""
    print("🚀 Запуск Smoke Test для Cortex v2")
    print("=" * 50)
    
    # Запуск всех тестов
    test_functions = [
        test_file_structure,
        test_doctrine_content, 
        test_credentials_content,
        test_packager_basic,
        test_packager_security_detection,
        test_full_context_integration
    ]
    
    results = []
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            results.append({
                "test_name": test_func.__name__,
                "status": "error",
                "details": {},
                "errors": [f"Неожиданная ошибка: {e}"]
            })
    
    # Генерация отчёта
    report = generate_report(results)
    
    # Сохранение отчёта
    report_path = "/opt/feature-factory/smoke_test_cortex_v2_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "=" * 50)
    print(f"📋 Отчёт сохранён: {report_path}")
    print("🏁 Smoke Test завершён")
    
    # Возвращаем код выхода
    overall_status = "success" if all(r["status"] in ["success", "warning"] for r in results) else "error"
    return 0 if overall_status == "success" else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)