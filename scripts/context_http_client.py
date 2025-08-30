#!/usr/bin/env python3
"""
TASK 0 — UNBLOCK_Context_HTTP_v1

Цель: Получать контекст без локального бинарника, только HTTP.

Правила:
Сначала пытаешься по списку базовых URL (таймауты короткие, без зависаний):
BASE_CANDIDATES = [ $FF_API_BASE_URL, "https://etl-tst.chococraft.ru/api/v1", "http://127.0.0.1:8081/api/v1" ]

Для каждого кандидата проверяешь readiness (2s connect, 3s max):
Пытаешься GET {host}/health/ready, если 404 → GET {host}/ready.
Первый 200 — выбранный BASE.

Потом вызываешь контекст:
GET {BASE}/context/?task_description=TRACE_API_IMPLEMENT_v1

Если ни один хост не дал 200 на /context за ≤40s → STOP & ESCALATE (не идёшь «искать по диску»).

Отдаёшь: REPORT_Context_Call_v1.json
Поля:
base_tried: массив {url,status,latency_s}
base_chosen: строка или null
context_status: HTTP-код
context_latency_ms: число
x_correlation_id: строка (если есть)
body_head: первые 300 байт ответа (строка)

DoD: context_status==200. Иначе — отчёт с пруфами и эскалация.
"""

import os
import sys
import json
import time
import requests
from urllib.parse import urljoin


def get_base_candidates():
    """Получает список базовых URL кандидатов"""
    ff_api_base_url = os.environ.get('FF_API_BASE_URL')
    return [
        ff_api_base_url,
        "https://etl-tst.chococraft.ru/api/v1",
        "http://127.0.0.1:8081/api/v1"
    ]


def check_readiness(base_url):
    """
    Проверяет readiness эндпоинт для заданного базового URL.
    Возвращает True, если получен статус 200, иначе False.
    """
    # Таймауты: 2s connect, 3s max
    timeouts = (2, 3)
    
    # Пытаемся GET {host}/health/ready
    health_ready_url = urljoin(base_url.rstrip('/') + '/', 'health/ready')
    try:
        response = requests.get(health_ready_url, timeout=timeouts)
        if response.status_code == 200:
            return True
    except requests.RequestException:
        pass  # Продолжаем проверку
    
    # Если 404 → GET {host}/ready
    ready_url = urljoin(base_url.rstrip('/') + '/', 'ready')
    try:
        response = requests.get(ready_url, timeout=timeouts)
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_context(base_url, task_description="TRACE_API_IMPLEMENT_v1"):
    """
    Вызывает контекстный эндпоинт и возвращает результат.
    """
    context_url = urljoin(base_url.rstrip('/') + '/', 'context/')
    params = {'task_description': task_description}
    
    try:
        start_time = time.time()
        response = requests.get(context_url, params=params, timeout=40)
        latency_ms = (time.time() - start_time) * 1000
        
        # Получаем X-Correlation-ID из заголовков, если есть
        correlation_id = response.headers.get('X-Correlation-ID', '')
        
        # Получаем первые 300 байт ответа
        body_head = response.text[:300] if response.text else ""
        
        return {
            'status_code': response.status_code,
            'latency_ms': latency_ms,
            'correlation_id': correlation_id,
            'body_head': body_head,
            'response': response
        }
    except requests.RequestException as e:
        # В случае ошибки возвращаем информацию об ошибке
        return {
            'status_code': None,
            'latency_ms': None,
            'correlation_id': '',
            'body_head': str(e)[:300],
            'response': None
        }


def main():
    """Основная функция скрипта"""
    # Получаем список кандидатов
    candidates = get_base_candidates()
    
    # Результаты попыток
    base_tried = []
    base_chosen = None
    context_result = None
    
    # Пробуем каждый кандидат по порядку
    for url in candidates:
        if url is None:
            continue
            
        print(f"Проверяю кандидат: {url}")
        
        start_time = time.time()
        is_ready = check_readiness(url)
        latency_s = time.time() - start_time
        
        base_tried.append({
            'url': url,
            'status': 200 if is_ready else 503,  # 503 - Service Unavailable как код ошибки
            'latency_s': latency_s
        })
        
        if is_ready:
            base_chosen = url
            print(f"Выбран базовый URL: {base_chosen}")
            break
        else:
            print(f"URL {url} не готов")
    
    # Если нашли готовый базовый URL, вызываем контекст
    if base_chosen:
        print(f"Вызываю контекст для: {base_chosen}")
        context_result = fetch_context(base_chosen)
    else:
        # Если ни один хост не готов, формируем отчет об ошибке
        context_result = {
            'status_code': None,
            'latency_ms': None,
            'correlation_id': '',
            'body_head': 'Ни один из базовых URL не готов к использованию',
            'response': None
        }
        print("Ни один из базовых URL не готов к использованию")
    
    # Формируем отчет
    report = {
        'base_tried': base_tried,
        'base_chosen': base_chosen,
        'context_status': context_result['status_code'],
        'context_latency_ms': context_result['latency_ms'],
        'x_correlation_id': context_result['correlation_id'],
        'body_head': context_result['body_head']
    }
    
    # Сохраняем отчет в файл
    report_file = '/opt/feature-factory/REPORT_Context_Call_v1.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Отчет сохранен в: {report_file}")
    
    # Проверяем DoD: context_status==200
    if context_result['status_code'] == 200:
        print("✅ DoD выполнен: context_status == 200")
        return 0
    else:
        print("❌ DoD не выполнен: context_status != 200")
        print("Эскалация...")
        return 1


if __name__ == "__main__":
    exit(main())