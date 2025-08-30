#!/usr/bin/env python3
"""
Скрипт для тестирования интеграции trace API в UI
"""

import requests
import json
import time

def test_ui_trace_integration():
    """Тестирует интеграцию trace API в UI"""
    
    results = {
        "ui_deployed": False,
        "api_working": False,
        "trace_endpoint_accessible": False,
        "ui_can_fetch_trace": False,
        "performance_ok": False
    }
    
    print("=== UI TRACE INTEGRATION TEST ===\n")
    
    # 1. Проверка доступности UI
    try:
        response = requests.get("https://etl-tst.chococraft.ru/", timeout=10)
        results["ui_deployed"] = response.status_code == 200
        print(f"1. UI доступен: {'✅' if results['ui_deployed'] else '❌'}")
    except Exception as e:
        print(f"1. UI доступен: ❌ ({e})")
    
    # 2. Проверка API
    try:
        response = requests.get("https://etl-tst.chococraft.ru/api/v1/health", timeout=10)
        results["api_working"] = response.status_code == 200
        print(f"2. API работает: {'✅' if results['api_working'] else '❌'}")
    except Exception as e:
        print(f"2. API работает: ❌ ({e})")
    
    # 3. Проверка trace endpoint
    try:
        response = requests.get("https://etl-tst.chococraft.ru/api/v1/tasks/task_timeline_demo/trace?limit=3", timeout=10)
        results["trace_endpoint_accessible"] = response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            trace_items = data.get("items", [])
            print(f"3. Trace endpoint: ✅ (получено {len(trace_items)} событий)")
            
            # Проверяем структуру данных
            if trace_items:
                sample_item = trace_items[0]
                required_fields = ["timestamp", "kind", "icon", "title", "description", "severity", "links", "details"]
                missing_fields = [field for field in required_fields if field not in sample_item]
                
                if not missing_fields:
                    results["ui_can_fetch_trace"] = True
                    print(f"4. Структура данных корректна: ✅")
                    print(f"   Пример: {sample_item['icon']} {sample_item['title']} - {sample_item['description'][:50]}...")
                else:
                    print(f"4. Структура данных: ❌ (отсутствуют поля: {missing_fields})")
            
        else:
            print(f"3. Trace endpoint: ❌ (статус {response.status_code})")
            
    except Exception as e:
        print(f"3. Trace endpoint: ❌ ({e})")
    
    # 4. Performance test
    if results["trace_endpoint_accessible"]:
        print("\n5. Тест производительности (10 запросов)...")
        latencies = []
        
        for i in range(10):
            start_time = time.time()
            try:
                response = requests.get("https://etl-tst.chococraft.ru/api/v1/tasks/task_timeline_demo/trace?limit=10", timeout=5)
                if response.status_code == 200:
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
            except:
                pass
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            results["performance_ok"] = max_latency < 500  # Разумный лимит для UI
            
            print(f"   Средняя задержка: {avg_latency:.1f}ms")
            print(f"   Максимальная: {max_latency:.1f}ms")
            print(f"   Performance OK: {'✅' if results['performance_ok'] else '❌'}")
    
    # Итоговый результат
    all_good = all(results.values())
    print(f"\n=== ИТОГОВЫЙ РЕЗУЛЬТАТ: {'✅ SUCCESS' if all_good else '⚠️ NEEDS ATTENTION'} ===")
    
    # Сохраняем детальный отчёт
    report = {
        "test_name": "UI_TRACE_INTEGRATION_TEST",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "success" if all_good else "warning",
        "results": results,
        "next_steps": [
            "Открыть https://etl-tst.chococraft.ru/tasks/task_timeline_demo для проверки UI",
            "Убедиться, что вкладка 'Трассировка выполнения' работает",
            "Проверить, что события отображаются с иконками"
        ] if all_good else [
            "Исправить найденные проблемы",
            "Повторить тест"
        ]
    }
    
    with open("UI_INTEGRATION_TEST_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return all_good

if __name__ == "__main__":
    success = test_ui_trace_integration()
    exit(0 if success else 1)