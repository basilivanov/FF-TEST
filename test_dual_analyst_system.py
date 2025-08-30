#!/usr/bin/env python3
"""
Интеграционный тест для системы двух аналитиков.
"""

import json
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.append('/opt/feature-factory')

def test_database_migration():
    """Тестирует, что миграция БД применена корректно."""
    print("🔍 Тестирование миграции БД...")
    
    db_path = "feature.test.db"
    if not os.path.exists(db_path):
        print("❌ БД не существует")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем наличие поля type
    cursor.execute("PRAGMA table_info(features)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'type' not in columns:
        print("❌ Поле 'type' не найдено в таблице features")
        return False
    
    print("✅ Поле 'type' присутствует в БД")
    
    # Тестируем ограничения
    try:
        cursor.execute("""
            INSERT INTO features (title, intent_json, status, priority, created_at, created_by, env, type)
            VALUES ('Test', '{}', 'NEW', 1, datetime('now'), 'test', 'test', 'INVALID')
        """)
        conn.commit()
        print("❌ Check constraint не работает")
        return False
    except sqlite3.IntegrityError:
        print("✅ Check constraint работает корректно")
    
    conn.close()
    return True

def test_llm_routing_config():
    """Тестирует конфигурацию LLM роутинга."""
    print("\n🔍 Тестирование конфигурации LLM роутинга...")
    
    config_path = "/opt/feature-factory/configs/llm_routing.yaml"
    if not os.path.exists(config_path):
        print("❌ Файл llm_routing.yaml не найден")
        return False
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    roles = config.get('roles', {})
    
    if 'InternalAnalyst' not in roles:
        print("❌ Роль InternalAnalyst не найдена")
        return False
    
    if 'BusinessAnalyst' not in roles:
        print("❌ Роль BusinessAnalyst не найдена")
        return False
    
    print("✅ Роли InternalAnalyst и BusinessAnalyst настроены")
    
    # Проверяем бюджеты
    budgets = config.get('budgets', {}).get('role_daily_tokens', {})
    if 'InternalAnalyst' not in budgets or 'BusinessAnalyst' not in budgets:
        print("❌ Бюджеты для аналитиков не настроены")
        return False
    
    print("✅ Бюджеты для аналитиков настроены")
    return True

def test_prompt_files():
    """Тестирует наличие файлов промптов."""
    print("\n🔍 Тестирование файлов промптов...")
    
    prompts_dir = Path("/opt/feature-factory/app/agents/prompts")
    
    internal_prompt = prompts_dir / "internal_analyst.md"
    business_prompt = prompts_dir / "business_analyst.md"
    
    if not internal_prompt.exists():
        print("❌ Файл internal_analyst.md не найден")
        return False
    
    if not business_prompt.exists():
        print("❌ Файл business_analyst.md не найден")
        return False
    
    print("✅ Файлы промптов существуют")
    
    # Проверяем содержимое
    with open(internal_prompt, 'r') as f:
        internal_content = f.read()
    
    if "INTERNAL" not in internal_content or "Internal Analyst" not in internal_content:
        print("❌ Некорректное содержимое internal_analyst.md")
        return False
    
    with open(business_prompt, 'r') as f:
        business_content = f.read()
    
    if "BUSINESS" not in business_content or "Business Analyst" not in business_content:
        print("❌ Некорректное содержимое business_analyst.md")
        return False
    
    print("✅ Содержимое промптов корректно")
    return True

def test_api_module():
    """Тестирует API модуль аналитиков."""
    print("\n🔍 Тестирование API модуля...")
    
    api_path = Path("/opt/feature-factory/app/api/analyst.py")
    if not api_path.exists():
        print("❌ Файл analyst.py не найден")
        return False
    
    print("✅ API модуль существует")
    
    # Проверяем, что API подключен в main.py
    main_path = Path("/opt/feature-factory/app/main.py")
    with open(main_path, 'r') as f:
        main_content = f.read()
    
    if "analyst_router" not in main_content:
        print("❌ Роутер аналитиков не подключен в main.py")
        return False
    
    print("✅ API роутер подключен в приложение")
    return True

def test_database_functionality():
    """Тестирует функциональность создания фич с типами."""
    print("\n🔍 Тестирование функциональности БД...")
    
    from sqlalchemy import create_engine, text
    
    os.environ['DATABASE_URL'] = 'sqlite:///./feature.test.db'
    engine = create_engine('sqlite:///./feature.test.db')
    
    # Тестовые данные
    test_internal = {
        'title': 'Test Internal Feature',
        'intent_json': json.dumps({'type': 'INTERNAL', 'description': 'test'}),
        'status': 'NEW',
        'priority': 1,
        'created_at': datetime.now(),
        'created_by': 'test',
        'env': 'test',
        'type': 'INTERNAL'
    }
    
    test_business = {
        'title': 'Test Business Feature',
        'intent_json': json.dumps({'type': 'BUSINESS', 'description': 'test'}),
        'status': 'NEW',
        'priority': 2,
        'created_at': datetime.now(),
        'created_by': 'test',
        'env': 'test',
        'type': 'BUSINESS'
    }
    
    with engine.connect() as conn:
        # Создаем внутреннюю фичу
        result = conn.execute(text("""
            INSERT INTO features (title, intent_json, status, priority, created_at, created_by, env, type)
            VALUES (:title, :intent_json, :status, :priority, :created_at, :created_by, :env, :type)
            RETURNING id
        """), test_internal)
        
        internal_id = result.fetchone()[0]
        
        # Создаем бизнес-фичу
        result = conn.execute(text("""
            INSERT INTO features (title, intent_json, status, priority, created_at, created_by, env, type)
            VALUES (:title, :intent_json, :status, :priority, :created_at, :created_by, :env, :type)
            RETURNING id
        """), test_business)
        
        business_id = result.fetchone()[0]
        
        conn.commit()
        
        # Проверяем созданные записи
        result = conn.execute(text("""
            SELECT id, title, type FROM features WHERE id IN (:internal_id, :business_id)
        """), {'internal_id': internal_id, 'business_id': business_id})
        
        records = result.fetchall()
        if len(records) != 2:
            print("❌ Не все записи созданы")
            return False
        
        types_found = [record[2] for record in records]
        if 'INTERNAL' not in types_found or 'BUSINESS' not in types_found:
            print("❌ Типы фич созданы некорректно")
            return False
    
    print("✅ Создание фич обоих типов работает корректно")
    return True

def run_all_tests():
    """Запускает все тесты."""
    print("🚀 Запуск интеграционных тестов системы двух аналитиков\n")
    
    tests = [
        test_database_migration,
        test_llm_routing_config,
        test_prompt_files,
        test_api_module,
        test_database_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} провалился: {e}")
    
    print(f"\n📊 Результаты: {passed}/{total} тестов прошло")
    
    if passed == total:
        print("🎉 Все тесты прошли! Система двух аналитиков реализована корректно.")
        return True
    else:
        print("⚠️  Некоторые тесты провалились. Требуются исправления.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)