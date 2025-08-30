#!/usr/bin/env python3
"""
TASK 0 — UNBLOCK_Context_HTTP_v1
TASK 1 — TRACE_API_REGISTER_AUDIT_v1

Скрипт для проверки доступности API и получения контекста через HTTP
"""

import os
import json
import time
import requests
from typing import List, Dict, Optional, Any

def get_base_candidates() -> List[str]:
    """Получить список кандидатов базовых URL"""
    candidates = []
    
    # Добавляем FF_API_BASE_URL если есть
    ff_api_base = os.environ.get('FF_API_BASE_URL')
    if ff_api_base:
        candidates.append(ff_api_base)
    
    # Добавляем стандартные кандидаты
    candidates.extend([
        "https://etl-tst.chococraft.ru/api/v1",
        "http://127.0.0.1:8081/api/v1"
    ])
    
    return candidates

def check_readiness(url: str) -> Dict[str, Any]:
    """Проверка готовности хоста"""
    start_time = time.time()
    result = {
        "url": url,
        "status": None,
        "latency_s": 0,
        "error": None
    }
    
    try:
        # Пробуем /health
        response = requests.get(
            f"{url}/health",
            timeout=(2, 3),  # 2s connect, 3s total
            allow_redirects=False
        )
        result["status"] = response.status_code
        result["latency_s"] = round(time.time() - start_time, 3)
        
        if response.status_code == 200:
            return result
            
    except requests.exceptions.RequestException as e:
        pass  # Продолжаем к корневому пути
    
    try:
        # Если /health не сработал, пробуем корневой путь
        response = requests.get(
            url.replace('/api/v1', '/'),
            timeout=(2, 3),
            allow_redirects=False
        )
        result["status"] = response.status_code
        result["latency_s"] = round(time.time() - start_time, 3)
        
    except requests.exceptions.RequestException as e:
        result["latency_s"] = round(time.time() - start_time, 3)
        result["error"] = str(e)
        result["status"] = 0  # Connection failed
    
    return result

def get_context(base_url: str) -> Dict[str, Any]:
    """Получение контекста от API"""
    start_time = time.time()
    result = {
        "context_status": None,
        "context_latency_ms": 0,
        "x_correlation_id": None,
        "body_head": "",
        "error": None
    }
    
    try:
        response = requests.get(
            f"{base_url}/context/",
            params={"task_description": "TRACE_API_IMPLEMENT_v1"},
            timeout=40
        )
        
        result["context_status"] = response.status_code
        result["context_latency_ms"] = round((time.time() - start_time) * 1000)
        result["x_correlation_id"] = response.headers.get("x-correlation-id")
        
        # Первые 300 байт ответа
        body_text = response.text if hasattr(response, 'text') else str(response.content)
        result["body_head"] = body_text[:300]
        
    except requests.exceptions.RequestException as e:
        result["context_latency_ms"] = round((time.time() - start_time) * 1000)
        result["error"] = str(e)
        result["context_status"] = 0
    
    return result

def check_trace_api(base_url: str) -> Dict[str, Any]:
    """Проверка существования trace API"""
    result = {
        "trace_path_exists": False,
        "needs_implementation": True,
        "openapi_checked": True,
        "proofs": []
    }
    
    # Проверяем OpenAPI spec
    openapi_proof = {"url": f"{base_url}/openapi.json", "status": None, "latency_ms": 0, "body_head": ""}
    start_time = time.time()
    
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        openapi_proof["status"] = response.status_code
        openapi_proof["latency_ms"] = round((time.time() - start_time) * 1000)
        openapi_proof["body_head"] = response.text[:300]
        
        if response.status_code == 200:
            # Ищем trace path в OpenAPI
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            trace_path_pattern = "/api/v1/tasks/{task_id}/trace"
            
            for path in paths.keys():
                if "trace" in path and "{task_id}" in path:
                    result["trace_path_exists"] = True
                    result["needs_implementation"] = False
                    break
                    
    except Exception as e:
        openapi_proof["latency_ms"] = round((time.time() - start_time) * 1000)
        openapi_proof["body_head"] = f"Error: {str(e)}"
    
    result["proofs"].append(openapi_proof)
    
    # Проверяем HTTP вызов trace endpoint
    trace_proof = {"url": f"{base_url}/tasks/task_timeline_demo/trace?limit=1", "status": None, "latency_ms": 0, "body_head": ""}
    start_time = time.time()
    
    try:
        response = requests.get(f"{base_url}/tasks/task_timeline_demo/trace", params={"limit": 1}, timeout=10)
        trace_proof["status"] = response.status_code
        trace_proof["latency_ms"] = round((time.time() - start_time) * 1000)
        trace_proof["body_head"] = response.text[:300]
        
        # Если не 404, то endpoint существует
        if response.status_code != 404:
            result["trace_path_exists"] = True
            result["needs_implementation"] = False
            
    except Exception as e:
        trace_proof["latency_ms"] = round((time.time() - start_time) * 1000)
        trace_proof["body_head"] = f"Error: {str(e)}"
    
    result["proofs"].append(trace_proof)
    
    return result

def main():
    """Основная логика выполнения задач"""
    print("Запуск TASK 0 — UNBLOCK_Context_HTTP_v1")
    
    # TASK 0: Проверка контекста
    candidates = get_base_candidates()
    base_tried = []
    base_chosen = None
    
    print(f"Проверяю кандидатов: {candidates}")
    
    for candidate in candidates:
        print(f"Проверяю готовность: {candidate}")
        readiness_result = check_readiness(candidate)
        base_tried.append(readiness_result)
        
        if readiness_result["status"] == 200:
            base_chosen = candidate
            print(f"Выбран базовый URL: {base_chosen}")
            break
    
    context_result = {}
    if base_chosen:
        print(f"Получаю контекст от {base_chosen}")
        context_result = get_context(base_chosen)
    else:
        print("Не найден рабочий базовый URL")
        context_result = {
            "context_status": None,
            "context_latency_ms": 0,
            "x_correlation_id": None,
            "body_head": "",
            "error": "No working base URL found"
        }
    
    # Формируем отчёт TASK 0
    context_report = {
        "base_tried": base_tried,
        "base_chosen": base_chosen,
        **context_result
    }
    
    # Сохраняем отчёт TASK 0
    with open("REPORT_Context_Call_v1.json", "w", encoding="utf-8") as f:
        json.dump(context_report, f, indent=2, ensure_ascii=False)
    
    print(f"Отчёт TASK 0 сохранён: context_status={context_result.get('context_status')}")
    
    # TASK 1: Проверка trace API (только если есть рабочий base)
    if base_chosen and context_result.get("context_status") == 200:
        print("\nЗапуск TASK 1 — TRACE_API_REGISTER_AUDIT_v1")
        trace_result = check_trace_api(base_chosen)
        
        # Сохраняем отчёт TASK 1
        with open("REPORT_TraceApi_Registration_v1.json", "w", encoding="utf-8") as f:
            json.dump(trace_result, f, indent=2, ensure_ascii=False)
        
        print(f"Отчёт TASK 1 сохранён: trace_path_exists={trace_result['trace_path_exists']}")
    else:
        print("TASK 1 пропущен: нет рабочего базового URL или context_status != 200")
        # Создаём пустой отчёт для TASK 1
        empty_trace_report = {
            "trace_path_exists": False,
            "needs_implementation": True,
            "openapi_checked": False,
            "proofs": [],
            "error": "No working base URL or context failed"
        }
        with open("REPORT_TraceApi_Registration_v1.json", "w", encoding="utf-8") as f:
            json.dump(empty_trace_report, f, indent=2, ensure_ascii=False)
    
    print("\nВыполнение завершено.")

if __name__ == "__main__":
    main()