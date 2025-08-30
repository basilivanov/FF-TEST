#!/usr/bin/env python3
"""
Интеграционный тест UI переключателя аналитиков.
"""

import requests
import json
import os
import time

def test_analyst_api_endpoints():
    """Тестирует API эндпоинты аналитиков."""
    print("🔍 Тестирование API эндпоинтов аналитиков...")
    
    api_base = os.getenv("FF_API_BASE_URL", "http://localhost:8081").rstrip("/")
    base_url = f"{api_base}/api/v1"
    
    # Тестируем внутреннего аналитика
    internal_payload = {
        "text": "Нужно добавить кэширование в API для улучшения производительности",
        "type": "INTERNAL"
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyst/create-intent",
            json=internal_payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Internal Analyst API работает")
            print(f"   Feature ID: {data.get('feature_id')}")
            print(f"   Type: {data.get('type')}")
            print(f"   Title: {data.get('title')}")
        else:
            print(f"❌ Internal Analyst API ошибка: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения с Internal Analyst API: {e}")
    
    # Небольшая пауза между запросами
    time.sleep(1)
    
    # Тестируем бизнес-аналитика
    business_payload = {
        "text": "Клиенты просят дашборд с аналитикой заказов",
        "type": "BUSINESS"
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyst/create-intent",
            json=business_payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Business Analyst API работает")
            print(f"   Feature ID: {data.get('feature_id')}")
            print(f"   Type: {data.get('type')}")
            print(f"   Title: {data.get('title')}")
        else:
            print(f"❌ Business Analyst API ошибка: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения с Business Analyst API: {e}")

def test_ui_deployment():
    """Проверяет доступность UI."""
    print("\n🔍 Проверка развертывания UI...")
    
    ui_url = "https://etl-tst.chococraft.ru"
    
    try:
        response = requests.get(ui_url, timeout=10, verify=False)
        if response.status_code == 200:
            print(f"✅ UI доступен по адресу {ui_url}")
            
            # Проверяем наличие обновленного контента
            if "Аналитики" in response.text or "analyst" in response.text.lower():
                print("✅ UI содержит обновления для аналитиков")
            else:
                print("⚠️  UI может не содержать обновления аналитиков")
        else:
            print(f"❌ UI недоступен: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка доступа к UI: {e}")

def test_server_availability():
    """Проверяет доступность API сервера."""
    print("\n🔍 Проверка доступности API сервера...")
    
    api_base = os.getenv("FF_API_BASE_URL", "http://localhost:8081").rstrip("/")
    try:
        response = requests.get(f"{api_base}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API сервер доступен")
            return True
        else:
            print(f"❌ API сервер недоступен: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API сервер недоступен: {e}")
        return False

def run_integration_tests():
    """Запускает интеграционные тесты."""
    print("🚀 Запуск интеграционных тестов UI переключателя аналитиков\n")
    
    # Проверяем доступность API сервера
    if not test_server_availability():
        print("\n❌ API сервер недоступен. Запустите сервер и повторите тесты.")
        return False
    
    # Тестируем API эндпоинты
    test_analyst_api_endpoints()
    
    # Проверяем UI
    test_ui_deployment()
    
    print("\n📊 Интеграционные тесты завершены!")
    print("\n🎯 Следующие шаги:")
    print("1. Откройте https://etl-tst.chococraft.ru")
    print("2. Перейдите на страницу Chat")
    print("3. Проверьте наличие переключателя 'Тип задачи'")
    print("4. Попробуйте отправить сообщения с разными типами")
    
    return True

if __name__ == "__main__":
    run_integration_tests()
