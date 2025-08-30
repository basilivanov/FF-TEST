#!/usr/bin/env python3
"""
Интеграционный тест конкурентного выполнения фич в реальной системе.
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime
import os
import sys

# Добавляем путь к приложению
sys.path.append('/opt/feature-factory')

from app.orchestrator.lock_manager import lock_manager

def create_test_features():
    """Создает две тестовые фичи через API."""
    
    # Используем существующую БД
    db_path = "/opt/feature-factory/test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Очищаем старые тестовые данные
    cursor.execute("DELETE FROM features WHERE created_by = 'concurrency_test'")
    cursor.execute("DELETE FROM tasks WHERE feature_id IN (SELECT id FROM features WHERE created_by = 'concurrency_test')")
    
    # Создаем первую фичу
    intent1 = {
        "title": "High Priority Feature",
        "description": "Feature that should run first due to high priority",
        "priority": 5
    }
    
    cursor.execute("""
        INSERT INTO features (title, intent_json, status, priority, created_by, env, type, created_at)
        VALUES (?, ?, 'NEW', ?, 'concurrency_test', 'test', 'BUSINESS', ?)
    """, ("High Priority Feature", json.dumps(intent1), 5, datetime.now()))
    
    feature1_id = cursor.lastrowid
    
    # Создаем вторую фичу  
    intent2 = {
        "title": "Low Priority Feature",
        "description": "Feature that should wait for first feature to complete",
        "priority": 1
    }
    
    cursor.execute("""
        INSERT INTO features (title, intent_json, status, priority, created_by, env, type, created_at) 
        VALUES (?, ?, 'NEW', ?, 'concurrency_test', 'test', 'BUSINESS', ?)
    """, ("Low Priority Feature", json.dumps(intent2), 1, datetime.now()))
    
    feature2_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    print(f"✅ Созданы тестовые фичи: ID {feature1_id} (приоритет 5) и ID {feature2_id} (приоритет 1)")
    return feature1_id, feature2_id

def check_features_status():
    """Проверяет текущий статус фич."""
    db_path = "/opt/feature-factory/test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, status, priority, plan_dsl_json
        FROM features 
        WHERE created_by = 'concurrency_test'
        ORDER BY priority DESC
    """)
    
    features = cursor.fetchall()
    
    print(f"\n📊 Статус фич:")
    for feature_id, title, status, priority, plan_dsl_json in features:
        has_plan = "есть план" if plan_dsl_json else "нет плана"
        print(f"  Фича {feature_id}: {title} (приоритет {priority}) -> {status} ({has_plan})")
    
    conn.close()
    return features

def check_lock_status():
    """Проверяет состояние блокировок."""
    status = lock_manager.get_status()
    print(f"\n🔒 Состояние блокировок:")
    print(f"  Активные блокировки: {status['active_locks']}")
    print(f"  Фичи с блокировками: {status['features_with_locks']}")
    print(f"  Всего заблокированных ресурсов: {status['total_locked_resources']}")

def simulate_orchestrator_cycle():
    """Симулирует один цикл работы оркестратора."""
    from app.orchestrator.loop import OrchestratorLoop
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.guard import get_db_connection_string
    
    # Подключаемся к реальной БД
    DATABASE_URL = get_db_connection_string()
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    orchestrator = OrchestratorLoop()
    
    async def run_cycle():
        session = SessionLocal()
        orchestrator.session = session
        
        try:
            print("\n🔄 Запуск цикла оркестратора...")
            
            # Обрабатываем новые фичи (NEW -> PLANNED)
            await orchestrator._process_new_features()
            
            # Обновляем статус фич (проверяем завершение)
            await orchestrator._check_and_update_feature_status()
            
        except Exception as e:
            print(f"❌ Ошибка в цикле оркестратора: {e}")
        finally:
            session.close()
    
    return run_cycle()

async def test_full_integration():
    """Полный интеграционный тест конкурентного выполнения."""
    print("🚀 Начинаем полный интеграционный тест конкурентного выполнения")
    print("=" * 70)
    
    # Очищаем состояние блокировок
    lock_manager._locks.clear()
    lock_manager._feature_locks.clear()
    
    # Создаем тестовые фичи
    feature1_id, feature2_id = create_test_features()
    
    # Проверяем начальное состояние
    print("\n📋 Начальное состояние:")
    check_features_status()
    check_lock_status()
    
    # Запускаем несколько циклов оркестратора
    for cycle in range(1, 4):
        print(f"\n🔄 === ЦИКЛ {cycle} ===")
        
        await simulate_orchestrator_cycle()
        
        print(f"\n📊 Состояние после цикла {cycle}:")
        features = check_features_status()
        check_lock_status()
        
        # Проверяем правила конкурентности
        running_features = [f for f in features if f[2] == 'RUNNING']
        planned_features = [f for f in features if f[2] == 'PLANNED']
        
        if len(running_features) > 1:
            print("❌ ОШИБКА: Одновременно выполняется больше одной фичи!")
            return False
        elif len(running_features) == 1:
            running_feature = running_features[0]
            print(f"✅ Выполняется фича {running_feature[0]}: {running_feature[1]}")
            
            if len(planned_features) > 0:
                print(f"✅ Фичи в ожидании: {[f[0] for f in planned_features]}")
        
        # Небольшая пауза между циклами
        await asyncio.sleep(0.5)
    
    # Симулируем завершение задач для проверки освобождения блокировок
    print(f"\n🎯 Симулируем завершение задач...")
    await simulate_task_completion(feature1_id)
    
    # Еще несколько циклов для проверки освобождения и запуска следующей фичи
    for cycle in range(4, 7):
        print(f"\n🔄 === ЦИКЛ {cycle} ===")
        
        await simulate_orchestrator_cycle()
        
        print(f"\n📊 Состояние после цикла {cycle}:")
        features = check_features_status()
        check_lock_status()
        
        # Проверяем что блокировки переходят между фичами
        running_features = [f for f in features if f[2] == 'RUNNING']
        if len(running_features) == 1:
            running_feature = running_features[0]
            print(f"✅ Теперь выполняется фича {running_feature[0]}: {running_feature[1]}")
        
        await asyncio.sleep(0.5)
    
    # Завершаем вторую фичу
    print(f"\n🎯 Завершаем вторую фичу...")
    await simulate_task_completion(feature2_id)
    
    # Финальный цикл
    print(f"\n🔄 === ФИНАЛЬНЫЙ ЦИКЛ ===")
    await simulate_orchestrator_cycle()
    
    print(f"\n📊 Финальное состояние:")
    features = check_features_status()
    check_lock_status()
    
    # Проверяем что все блокировки освобождены
    final_status = lock_manager.get_status()
    if final_status['total_locked_resources'] == 0:
        print("✅ Все блокировки корректно освобождены")
    else:
        print(f"❌ Остались активные блокировки: {final_status['active_locks']}")
        return False
    
    # Проверяем что обе фичи завершены
    done_features = [f for f in features if f[2] == 'DONE']
    if len(done_features) == 2:
        print("✅ Обе фичи успешно завершены")
    else:
        print(f"❌ Не все фичи завершены. DONE: {len(done_features)}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 ПОЛНЫЙ ИНТЕГРАЦИОННЫЙ ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("🚀 Диспетчер Блокировок обеспечивает корректное последовательное выполнение фич")
    
    return True

async def simulate_task_completion(feature_id: int):
    """Симулирует завершение всех задач фичи."""
    db_path = "/opt/feature-factory/test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Помечаем все задачи фичи как завершенные
    cursor.execute("""
        UPDATE tasks 
        SET status = 'DONE', finished_at = ?
        WHERE feature_id = ? AND status != 'DONE'
    """, (datetime.now(), feature_id))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ Завершено {affected} задач для фичи {feature_id}")

def cleanup_test_data():
    """Очищает тестовые данные."""
    db_path = "/opt/feature-factory/test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tasks WHERE feature_id IN (SELECT id FROM features WHERE created_by = 'concurrency_test')")
    cursor.execute("DELETE FROM features WHERE created_by = 'concurrency_test'")
    
    conn.commit()
    conn.close()
    
    print("🧹 Тестовые данные очищены")

async def main():
    """Главная функция тестирования."""
    try:
        success = await test_full_integration()
        if success:
            return 0
        else:
            return 1
    except Exception as e:
        print(f"💥 Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup_test_data()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)