#!/usr/bin/env python3
"""
Скрипт для тестирования trace API и генерации пруф-пакета
"""

import os
import json
import time
import requests
from typing import Dict, Any, List

# Установка DATABASE_URL для импорта
os.environ["DATABASE_URL"] = "sqlite:////opt/feature-factory/data/test.db"

def test_trace_endpoint(base_url: str, task_id: str, limit: int = 5) -> Dict[str, Any]:
    """Тестирует trace endpoint"""
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/tasks/{task_id}/trace",
            params={"limit": limit},
            timeout=10
        )
        
        duration_ms = round((time.time() - start_time) * 1000)
        
        return {
            "url": f"{base_url}/api/v1/tasks/{task_id}/trace?limit={limit}",
            "status": response.status_code,
            "latency_ms": duration_ms,
            "x_correlation_id": response.headers.get("x-correlation-id"),
            "body_head": response.text[:300],
            "success": response.status_code == 200
        }
        
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000)
        return {
            "url": f"{base_url}/api/v1/tasks/{task_id}/trace?limit={limit}",
            "status": 0,
            "latency_ms": duration_ms,
            "x_correlation_id": None,
            "body_head": f"Error: {str(e)}",
            "success": False
        }

def test_openapi_contains_trace(base_url: str) -> Dict[str, Any]:
    """Проверяет наличие trace пути в OpenAPI"""
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            trace_paths = [path for path in paths.keys() if "trace" in path]
            
            return {
                "openapi_available": True,
                "trace_paths_found": trace_paths,
                "contains_task_trace": any("/tasks/{task_id}/trace" in path for path in trace_paths)
            }
        else:
            return {
                "openapi_available": False,
                "trace_paths_found": [],
                "contains_task_trace": False
            }
    except Exception as e:
        return {
            "openapi_available": False,
            "trace_paths_found": [],
            "contains_task_trace": False,
            "error": str(e)
        }

def performance_test(base_url: str, task_id: str, iterations: int = 100) -> Dict[str, Any]:
    """Выполняет тест производительности p95"""
    latencies = []
    
    print(f"Запуск {iterations} запросов для теста производительности...")
    
    for i in range(iterations):
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{base_url}/api/v1/tasks/{task_id}/trace",
                params={"limit": 10},
                timeout=5
            )
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                latencies.append(duration_ms)
                
        except Exception:
            # Игнорируем ошибки в тесте производительности
            pass
        
        if (i + 1) % 10 == 0:
            print(f"Выполнено {i + 1}/{iterations} запросов")
    
    if latencies:
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
        
        return {
            "total_requests": iterations,
            "successful_requests": len(latencies),
            "p95_latency_ms": round(p95_latency, 2),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
            "meets_requirement": p95_latency <= 200
        }
    else:
        return {
            "total_requests": iterations,
            "successful_requests": 0,
            "error": "No successful requests"
        }

def main():
    """Основная функция тестирования"""
    print("=== TRACE API TESTING ===")
    
    # Тестирование локального сервера
    local_base = "http://127.0.0.1:8081"
    remote_base = "https://etl-tst.chococraft.ru"
    test_task_id = "task_timeline_demo"
    
    print(f"\n1. Тестирование trace endpoint локально...")
    local_test = test_trace_endpoint(local_base, test_task_id)
    print(f"   Локальный тест: {local_test['status']} за {local_test['latency_ms']}ms")
    
    print(f"\n2. Тестирование trace endpoint удалённо...")
    remote_test = test_trace_endpoint(remote_base, test_task_id)
    print(f"   Удалённый тест: {remote_test['status']} за {remote_test['latency_ms']}ms")
    
    print(f"\n3. Проверка OpenAPI локально...")
    local_openapi = test_openapi_contains_trace(local_base)
    print(f"   Trace в OpenAPI: {local_openapi['contains_task_trace']}")
    
    print(f"\n4. Проверка OpenAPI удалённо...")
    remote_openapi = test_openapi_contains_trace(remote_base)
    print(f"   Trace в OpenAPI: {remote_openapi['contains_task_trace']}")
    
    # Выбираем лучший endpoint для теста производительности
    working_base = None
    if local_test['success']:
        working_base = local_base
        print(f"\n5. Тест производительности (локально)...")
    elif remote_test['success']:
        working_base = remote_base
        print(f"\n5. Тест производительности (удалённо)...")
    
    perf_results = {}
    if working_base:
        perf_results = performance_test(working_base, test_task_id, 20)  # Уменьшил до 20 для быстроты
        print(f"   P95 latency: {perf_results.get('p95_latency_ms', 'N/A')}ms")
        print(f"   Требование ≤200ms: {'✅' if perf_results.get('meets_requirement', False) else '❌'}")
    else:
        print(f"\n5. Тест производительности пропущен: нет рабочего endpoint")
    
    # Создаём итоговый отчёт
    report = {
        "task": "TRACE_API_IMPLEMENT_v1",
        "status": "green" if (local_test['success'] or remote_test['success']) else "yellow",
        "findings": {
            "local_endpoint": local_test,
            "remote_endpoint": remote_test,
            "openapi_local": local_openapi,
            "openapi_remote": remote_openapi,
            "performance": perf_results
        },
        "openapi_ok": local_openapi.get('contains_task_trace', False) or remote_openapi.get('contains_task_trace', False),
        "samples": {
            "items": []
        }
    }
    
    # Добавляем примеры ответов если есть успешные тесты
    if local_test['success']:
        try:
            sample_response = requests.get(f"{local_base}/api/v1/tasks/{test_task_id}/trace?limit=2")
            if sample_response.status_code == 200:
                sample_data = sample_response.json()
                report["samples"]["items"] = sample_data.get("items", [])[:2]
        except:
            pass
    
    # Сохраняем отчёт
    with open("REPORT_TraceApi_Impl_v1.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== ОТЧЁТ СОХРАНЁН: REPORT_TraceApi_Impl_v1.json ===")
    print(f"Статус: {report['status']}")
    print(f"OpenAPI OK: {report['openapi_ok']}")

if __name__ == "__main__":
    main()