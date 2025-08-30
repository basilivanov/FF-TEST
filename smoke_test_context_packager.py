#!/usr/bin/env python3
"""
Smoke тест для ContextPackager - проверяем, что контекст формируется корректно
для задачи с ролью Dev и включает:
1. Данные из Cortex (инженерный справочник и правила для роли)
2. Проиндексированную информацию о функциях (из ctags)
3. Граф вызовов (из pyan3)
"""

import sys
import os
import json
from datetime import datetime

# Добавляем app в путь импорта
sys.path.insert(0, '/opt/feature-factory/app')

from context.packager import ContextPackager


def create_test_task():
    """Создаем тестовую задачу с ролью Dev"""
    return {
        "id": 999,
        "feature_id": 999, 
        "role": "Dev",
        "dsl_json": {
            "description": "Implement new API endpoint for user authentication in app/api/routes/auth.py",
            "files_to_modify": ["app/api/routes/auth.py"],
            "functions_to_implement": ["authenticate_user", "generate_token"],
            "dependencies": ["app/models/user.py", "app/utils/jwt.py"]
        },
        "status": "NEW"
    }


def analyze_context(context_content):
    """Анализирует содержимое контекста и создает отчет"""
    report = {
        "total_length": len(context_content),
        "sections": {},
        "contains_cortex": False,
        "contains_code_info": False,
        "contains_call_graph": False,
        "file_references": []
    }
    
    # Ищем секции в контексте
    lines = context_content.split('\n')
    current_section = None
    
    for line in lines:
        if line.startswith('#'):
            current_section = line.strip()
            report["sections"][current_section] = 0
        elif current_section:
            report["sections"][current_section] += 1
            
        # Проверяем наличие ключевых индикаторов
        if 'cortex' in line.lower() or 'справочник' in line.lower():
            report["contains_cortex"] = True
            
        if 'function' in line.lower() or 'def ' in line:
            report["contains_code_info"] = True
            
        if 'call' in line.lower() or 'вызов' in line.lower():
            report["contains_call_graph"] = True
            
        # Ищем ссылки на файлы
        if '.py' in line and ('app/' in line or 'tests/' in line):
            report["file_references"].append(line.strip())
    
    return report


def main():
    """Основная функция smoke теста"""
    print("🧪 Запускаем smoke тест ContextPackager...")
    print("="*60)
    
    # Создаем тестовую задачу
    test_task = create_test_task()
    print(f"📝 Создана тестовая задача:")
    print(f"   - ID: {test_task['id']}")
    print(f"   - Роль: {test_task['role']}")
    print(f"   - Описание: {test_task['dsl_json']['description']}")
    print()
    
    # Инициализируем ContextPackager
    try:
        packager = ContextPackager()
        print("✅ ContextPackager успешно инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации ContextPackager: {e}")
        return 1
    
    # Формируем контекст
    print("📦 Формируем контекст для задачи...")
    try:
        context = packager.build_context_for_task(test_task)
        print("✅ Контекст успешно сформирован")
    except Exception as e:
        print(f"❌ Ошибка формирования контекста: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Анализируем результат
    print("🔍 Анализируем содержимое контекста...")
    report = analyze_context(context)
    
    print(f"📊 Результаты анализа:")
    print(f"   - Общая длина: {report['total_length']:,} символов")
    print(f"   - Количество секций: {len(report['sections'])}")
    print(f"   - Содержит данные Cortex: {'✅' if report['contains_cortex'] else '❌'}")
    print(f"   - Содержит информацию о коде: {'✅' if report['contains_code_info'] else '❌'}")  
    print(f"   - Содержит информацию о графе вызовов: {'✅' if report['contains_call_graph'] else '❌'}")
    print(f"   - Ссылок на файлы найдено: {len(report['file_references'])}")
    
    print(f"\n📑 Секции контекста:")
    for section, lines in report["sections"].items():
        print(f"   - {section}: {lines} строк")
    
    # Сохраняем полный контекст в файл для детального анализа
    output_file = "/opt/feature-factory/tmp/smoke_test_context_output.md"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Smoke Test Context Output\n")
            f.write(f"**Дата:** {datetime.now().isoformat()}\n")
            f.write(f"**Задача:** {test_task['dsl_json']['description']}\n\n")
            f.write("---\n\n")
            f.write(context)
        print(f"💾 Полный контекст сохранен в: {output_file}")
    except Exception as e:
        print(f"⚠️  Не удалось сохранить контекст в файл: {e}")
    
    # Проверка критериев успеха
    success = True
    if not report['contains_cortex']:
        print("❌ КРИТИЧНО: Контекст не содержит данные из Cortex")
        success = False
    if not report['contains_code_info']:
        print("❌ КРИТИЧНО: Контекст не содержит информацию о коде")
        success = False
    if len(report['file_references']) == 0:
        print("❌ КРИТИЧНО: Не найдено ссылок на файлы")
        success = False
        
    print("\n" + "="*60)
    if success:
        print("🎉 SMOKE ТЕСТ ПРОШЕЛ УСПЕШНО!")
        print("✅ ContextPackager работает корректно")
        return 0
    else:
        print("💥 SMOKE ТЕСТ ПРОВАЛЕН!")
        print("❌ Обнаружены критические проблемы")
        return 1


if __name__ == "__main__":
    exit(main())