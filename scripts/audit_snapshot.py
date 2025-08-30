#!/usr/bin/env python3
"""
Аудит-снапшот для проверки текущего состояния системы.
"""

import json
import os
import subprocess
import sys
from typing import Dict, Any

def run_command(command: str) -> Dict[str, Any]:
    """Выполняет команду и возвращает результат."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout"
        }
    except Exception as e:
        return {
            "command": command,
            "returncode": -2,
            "stdout": "",
            "stderr": str(e)
        }

def check_http_endpoint(url: str) -> Dict[str, Any]:
    """Проверяет HTTP эндпоинт."""
    try:
        # Используем curl для проверки эндпоинта
        command = f"curl -s -w '%{{http_code}}' -o /dev/null '{url}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            status_code = result.stdout.strip()
            return {
                "url": url,
                "status": int(status_code) if status_code.isdigit() else 0,
                "success": status_code.startswith('2') or status_code.startswith('3')
            }
        else:
            return {
                "url": url,
                "status": 0,
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "success": False,
            "error": str(e)
        }

def main():
    """Основная функция для создания аудит-снапшота."""
    
    # Проверим доступность API эндпоинтов
    api_checks = []
    
    # Проверим базовые эндпоинты
    base_endpoints = [
        "http://localhost:8081/api/v1/index/calls?limit=1",
        "http://localhost:8081/api/v1/logs?limit=1"
    ]
    
    for endpoint in base_endpoints:
        api_checks.append(check_http_endpoint(endpoint))
    
    # Проверим целевой эндпоинт трассировки задач
    trace_endpoint = "http://localhost:8081/api/v1/tasks/task_timeline_demo/trace?limit=1"
    trace_check = check_http_endpoint(trace_endpoint)
    api_checks.append(trace_check)
    
    # Проверим количество событий в БД для демонстрационной задачи
    db_check = run_command("sqlite3 /opt/feature-factory/data/test.db \"SELECT COUNT(*) FROM agent_events WHERE task_id = 'task_timeline_demo';\"")
    
    # Создадим отчет
    report = {
        "api": {
            "trace_path_exists": trace_check["success"]
        },
        "db": {
            "events_for_demo": 0
        },
        "proofs": api_checks
    }
    
    # Попробуем получить количество событий из результата команды
    try:
        if db_check["returncode"] == 0 and db_check["stdout"]:
            count = int(db_check["stdout"])
            report["db"]["events_for_demo"] = count
    except:
        pass
    
    # Добавим результат проверки БД в пруфы
    report["proofs"].append({
        "type": "db_check",
        "query": "SELECT COUNT(*) FROM agent_events WHERE task_id = 'task_timeline_demo'",
        "result": db_check
    })
    
    # Выведем отчет в формате JSON
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()