#!/usr/bin/env python3
"""
Простой E2E тест для проверки работы планировщика с реальными задачами.
"""

import requests
import time
import json
import os

api_base = os.getenv("FF_API_BASE_URL", "http://localhost:8081").rstrip("/")
BASE_URL = f"{api_base}/api/v1/orchestrator"

def test_scheduler_with_real_architect():
    """Тест с настоящим Архитектором"""
    
    print("=== E2E тест планировщика с настоящим Архитектором ===")
    
    # 1. Создаем feature с autostart=False для контролируемого тестирования
    feature_data = {
        "title": f"test-real-architect-ping-{int(time.time())}",
        "description": "Test with real Architect LLM",
        "intent": {
            "goal": "Create a simple ping endpoint that returns {ping: pong}",
            "requirements": ["Add /api/v1/ping endpoint", "Return JSON response", "Use FastAPI"]
        },
        "autostart": False
    }
    
    print("1. Создаем feature...")
    response = requests.post(f"{BASE_URL}/features", json=feature_data)
    if response.status_code != 200:
        print(f"❌ Ошибка создания feature: {response.text}")
        return
    
    feature = response.json()
    feature_id = feature["id"]
    print(f"✅ Feature создан: ID={feature_id}")
    
    # 2. Запускаем планирование
    print("2. Запускаем планирование...")
    response = requests.post(f"{BASE_URL}/features/{feature_id}/plan")
    if response.status_code != 200:
        print(f"❌ Ошибка планирования: {response.text}")
        return
        
    plan = response.json()
    print(f"✅ План создан: {len(plan['tasks'])} задач")
    for task in plan['tasks']:
        print(f"   - {task['role']}: {task.get('name', 'N/A')}")
    
    # 3. Запускаем выполнение
    print("3. Запускаем выполнение...")
    response = requests.post(f"{BASE_URL}/features/{feature_id}/run")
    if response.status_code != 200:
        print(f"❌ Ошибка запуска выполнения: {response.text}")
        return
        
    run = response.json()
    run_id = run["run_id"]
    print(f"✅ Выполнение запущено: run_id={run_id}")
    
    # 4. Ждем завершения (с таймаутом)
    print("4. Ожидаем завершения...")
    max_wait = 180  # 3 минуты
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/graph/{run_id}/status")
        if response.status_code != 200:
            print(f"❌ Ошибка получения статуса: {response.text}")
            return
            
        status = response.json()
        feature_status = status.get("feature_status", "UNKNOWN")
        print(f"   Статус: {feature_status}")
        
        if feature_status == "DONE":
            print("✅ Выполнение завершено успешно!")
            return True
        elif feature_status in ["FAILED", "ERROR"]:
            print(f"❌ Выполнение завершилось с ошибкой: {feature_status}")
            print(f"   Подробности: {json.dumps(status, indent=2, ensure_ascii=False)}")
            return False
            
        time.sleep(5)  # Проверяем каждые 5 секунд
    
    print(f"⏰ Превышен таймаут {max_wait} секунд")
    return False

if __name__ == "__main__":
    success = test_scheduler_with_real_architect()
    exit(0 if success else 1)
