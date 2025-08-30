#!/usr/bin/env python3
"""
Создание задачи для демонстрации трассировки выполнения задачи.
"""

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta

def generate_test_events(task_id: str = "task_timeline_demo", count: int = 10):
    """Генерирует тестовые события для демонстрации трассировки задачи."""
    
    # Создаем подключение к базе данных
    db_path = "/opt/feature-factory/data/test.db"
    
    # Типы событий и их описания
    event_types = [
        {
            "event": "task_started",
            "agent_role": "Architect",
            "details": {
                "actor": "Architect",
                "env": "test"
            }
        },
        {
            "event": "context_pack_built",
            "agent_role": "ContextPackager",
            "details": {
                "pack_bytes": 4567,
                "selectors": ["admin/logs"]
            }
        },
        {
            "event": "llm_call_start",
            "agent_role": "Dev",
            "details": {
                "model": "claude-3.5-sonnet",
                "provider": "anthropic",
                "role": "Dev"
            }
        },
        {
            "event": "llm_call_end",
            "agent_role": "Dev",
            "details": {
                "input_tokens": 1250,
                "output_tokens": 842,
                "duration_ms": 1250
            }
        },
        {
            "event": "tool_apply",
            "agent_role": "Dev",
            "details": {
                "tool_name": "write_file",
                "file_path": "/app/main.py"
            }
        },
        {
            "event": "watchdog_triggered",
            "agent_role": "Watchdog",
            "details": {
                "reason": "anti-loop",
                "context": "Codex: анти-зацикливание"
            }
        },
        {
            "event": "qa_run_start",
            "agent_role": "QA",
            "details": {
                "test_suite": "unit_tests"
            }
        },
        {
            "event": "qa_run_end_fail",
            "agent_role": "QA",
            "details": {
                "failed": 1,
                "passed": 12,
                "test_name": "Playwright test"
            }
        },
        {
            "event": "task_done",
            "agent_role": "Orchestrator",
            "details": {
                "status": "completed",
                "final_result": "success"
            }
        }
    ]
    
    # Создаем события с разными временными метками
    events = []
    now = datetime.now()
    
    for i in range(min(count, len(event_types))):
        event_time = now - timedelta(minutes=count-i)
        event_data = event_types[i].copy()
        event_data["ts"] = event_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Добавляем correlation_id в details
        correlation_id = f"corr-{uuid.uuid4().hex[:8]}"
        event_data["details"]["correlation_id"] = correlation_id
        
        # Если это событие с артефактом, добавляем путь к артефакту
        if event_data["event"] in ["context_pack_built", "tool_apply"]:
            event_data["details"]["artifact_path"] = f"/artifacts/{task_id}/{event_data['event']}.json"
        
        events.append(event_data)
    
    # Добавляем дополнительные события, если count больше, чем количество типов событий
    if count > len(event_types):
        for i in range(len(event_types), count):
            event_time = now - timedelta(minutes=count-i)
            event_data = {
                "event": f"custom_event_{i}",
                "agent_role": "Dev",
                "ts": event_time.strftime('%Y-%m-%d %H:%M:%S'),
                "details": {
                    "description": f"Custom event {i}",
                    "value": i * 10
                }
            }
            # Добавляем correlation_id в details
            correlation_id = f"corr-{uuid.uuid4().hex[:8]}"
            event_data["details"]["correlation_id"] = correlation_id
            events.append(event_data)
    
    # Вставляем события в базе данных
    for event in events:
        # Подготавливаем SQL-запрос
        details_json = json.dumps(event['details']).replace('"', '""')  # Экранируем кавычки для SQL
        query = f"INSERT INTO agent_events (ts, agent_role, task_id, event, details_json) VALUES ('{event['ts']}', '{event['agent_role']}', '{task_id}', '{event['event']}', '{details_json}');"
        
        # Выполняем запрос
        result = subprocess.run(f"sqlite3 {db_path} \"{query}\"", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error inserting event: {result.stderr}")
            return False
    
    print(f"Сгенерировано {len(events)} тестовых событий для задачи {task_id}")
    return True

def main():
    """Основная функция для создания задачи демонстрации."""
    task_id = "task_timeline_demo"
    
    # Генерируем тестовые события
    if generate_test_events(task_id, 10):
        print(f"Задача {task_id} успешно создана с тестовыми событиями")
    else:
        print(f"Ошибка при создании задачи {task_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()