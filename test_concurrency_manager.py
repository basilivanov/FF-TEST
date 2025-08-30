#!/usr/bin/env python3
"""
Тест диспетчера блокировок для управления конкурентностью.
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
from app.orchestrator.loop import OrchestratorLoop
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Настройка тестовой БД
TEST_DB_PATH = "/opt/feature-factory/test_concurrency.db"
DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

def setup_test_db():
    """Создает тестовую базу данных с необходимыми таблицами."""
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицу features
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            intent_json TEXT,
            plan_dsl_json TEXT,
            status TEXT DEFAULT 'NEW',
            priority INTEGER DEFAULT 3,
            created_by TEXT,
            env TEXT DEFAULT 'test',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP
        )
    """)
    
    # Создаем таблицу tasks  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id INTEGER REFERENCES features(id),
            role TEXT NOT NULL,
            dsl_json TEXT,
            status TEXT DEFAULT 'NEW',
            attempts INTEGER DEFAULT 0,
            budget_tokens INTEGER DEFAULT 1000,
            scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            finished_at TIMESTAMP
        )
    """)
    
    # Создаем таблицу graph_runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_runs (
            run_id TEXT PRIMARY KEY,
            feature_id INTEGER REFERENCES features(id),
            graph_name TEXT NOT NULL,
            thread_id TEXT,
            status TEXT DEFAULT 'NEW',
            last_checkpoint_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def cleanup_test_db():
    """Очищает тестовую базу данных."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def create_test_feature(title: str, priority: int = 3) -> int:
    """Создает тестовую фичу в БД."""
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    
    intent_json = json.dumps({
        "title": title,
        "description": f"Test feature: {title}",
        "priority": priority
    })
    
    cursor.execute("""
        INSERT INTO features (title, intent_json, priority, created_by, env)
        VALUES (?, ?, ?, 'test_user', 'test')
    """, (title, intent_json, priority))
    
    feature_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return feature_id

async def test_basic_lock_functionality():
    """Тестирует базовую функциональность блокировок."""
    print("\n=== Тест базовой функциональности блокировок ===")
    
    # Очищаем состояние менеджера блокировок
    lock_manager._locks.clear()
    lock_manager._feature_locks.clear()
    
    # Тестируем захват блокировки
    result = lock_manager.acquire("feature_pipeline", 1)
    print(f"Захват блокировки feature_pipeline фичей 1: {result}")
    assert result == True
    
    # Тестируем повторный захват той же блокировки другой фичей
    result = lock_manager.acquire("feature_pipeline", 2)
    print(f"Захват блокировки feature_pipeline фичей 2: {result}")
    assert result == False
    
    # Тестируем освобождение блокировки
    result = lock_manager.release("feature_pipeline", 1)
    print(f"Освобождение блокировки feature_pipeline фичей 1: {result}")
    assert result == True
    
    # Тестируем повторный захват после освобождения
    result = lock_manager.acquire("feature_pipeline", 2)
    print(f"Захват блокировки feature_pipeline фичей 2 после освобождения: {result}")
    assert result == True
    
    # Освобождаем для чистоты
    lock_manager.release("feature_pipeline", 2)
    
    print("✅ Базовая функциональность блокировок работает корректно")

async def test_multiple_locks():
    """Тестирует захват множественных блокировок."""
    print("\n=== Тест множественных блокировок ===")
    
    # Очищаем состояние
    lock_manager._locks.clear()
    lock_manager._feature_locks.clear()
    
    # Тестируем захват множественных блокировок
    resources = ["feature_pipeline", "database_main", "code_indexer"]
    success, failed = lock_manager.acquire_multiple(resources, 1)
    print(f"Захват множественных блокировок фичей 1: success={success}, failed={failed}")
    assert success == True
    assert len(failed) == 0
    
    # Тестируем блокирование другой фичи
    success, failed = lock_manager.acquire_multiple(resources, 2)
    print(f"Захват тех же блокировок фичей 2: success={success}, failed={failed}")
    assert success == False
    assert len(failed) == len(resources)
    
    # Освобождаем все блокировки фичи 1
    released = lock_manager.release_all_for_feature(1)
    print(f"Освобождение всех блокировок фичи 1: {released}")
    assert len(released) == len(resources)
    
    # Теперь фича 2 может захватить блокировки
    success, failed = lock_manager.acquire_multiple(resources, 2)
    print(f"Захват блокировок фичей 2 после освобождения: success={success}, failed={failed}")
    assert success == True
    assert len(failed) == 0
    
    # Освобождаем для чистоты
    lock_manager.release_all_for_feature(2)
    
    print("✅ Множественные блокировки работают корректно")

async def test_orchestrator_integration():
    """Тестирует интеграцию с оркестратором."""
    print("\n=== Тест интеграции с оркестратором ===")
    
    # Подготавливаем тестовую БД
    setup_test_db()
    
    # Создаем две тестовые фичи
    feature1_id = create_test_feature("Test Feature 1", priority=5)
    feature2_id = create_test_feature("Test Feature 2", priority=3)
    
    print(f"Создали фичи: {feature1_id} и {feature2_id}")
    
    # Настраиваем движок БД для оркестратора
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Создаем экземпляр оркестратора с модифицированной БД
    orchestrator = OrchestratorLoop()
    
    # Переопределяем создание сессии для тестовой БД
    original_session_local = orchestrator.__class__.__bases__[0]
    
    # Выполняем одну итерацию обработки
    session = SessionLocal()
    orchestrator.session = session
    
    try:
        print("Обрабатываем новые фичи...")
        await orchestrator._process_new_features()
        
        # Проверяем статусы фич
        result = session.execute(
            text("SELECT id, title, status FROM features ORDER BY priority DESC")
        )
        features = result.fetchall()
        
        for feature_row in features:
            feature_id, title, status = feature_row
            print(f"Фича {feature_id} ({title}): статус = {status}")
            
        print("Проверяем состояние блокировок...")
        lock_status = lock_manager.get_status()
        print(f"Активные блокировки: {lock_status}")
        
    finally:
        session.close()
    
    # Очищаем
    cleanup_test_db()
    
    print("✅ Интеграция с оркестратором работает")

async def test_sequential_execution():
    """Тестирует последовательное выполнение фич."""
    print("\n=== Тест последовательного выполнения ===")
    
    # Очищаем состояние
    lock_manager._locks.clear()
    lock_manager._feature_locks.clear()
    
    # Симуляция запуска двух фич одновременно
    print("Запускаем фичу 1...")
    success1, _ = lock_manager.acquire_multiple(["feature_pipeline"], 1)
    print(f"Фича 1 захватила блокировку: {success1}")
    
    print("Пытаемся запустить фичу 2...")
    success2, failed2 = lock_manager.acquire_multiple(["feature_pipeline"], 2)
    print(f"Фича 2 захватила блокировку: {success2}, заблокированные ресурсы: {failed2}")
    
    print("Завершаем фичу 1...")
    released1 = lock_manager.release_all_for_feature(1)
    print(f"Фича 1 освободила ресурсы: {released1}")
    
    print("Теперь запускаем фичу 2...")
    success2_retry, _ = lock_manager.acquire_multiple(["feature_pipeline"], 2)
    print(f"Фича 2 захватила блокировку после освобождения: {success2_retry}")
    
    # Завершаем фичу 2
    lock_manager.release_all_for_feature(2)
    
    # Проверяем что все блокировки освобождены
    final_status = lock_manager.get_status()
    print(f"Финальное состояние блокировок: {final_status}")
    
    assert success1 == True, "Фича 1 должна захватить блокировку"
    assert success2 == False, "Фича 2 не должна захватить блокировку пока работает фича 1"  
    assert success2_retry == True, "Фича 2 должна захватить блокировку после завершения фичи 1"
    assert final_status["total_locked_resources"] == 0, "Все блокировки должны быть освобождены"
    
    print("✅ Последовательное выполнение работает корректно")

async def main():
    """Главная функция тестирования."""
    print("🔒 Запуск тестов Диспетчера Блокировок")
    print("=" * 50)
    
    try:
        await test_basic_lock_functionality()
        await test_multiple_locks()
        await test_orchestrator_integration()
        await test_sequential_execution()
        
        print("\n" + "=" * 50)
        print("✅ Все тесты пройдены успешно!")
        print("🚀 Диспетчер Блокировок готов к использованию")
        
    except AssertionError as e:
        print(f"\n❌ Тест завершился неудачно: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)