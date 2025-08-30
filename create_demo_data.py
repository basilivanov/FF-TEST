#!/usr/bin/env python3
"""
Создание демо данных для trace API
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta

# Устанавливаем DATABASE_URL
os.environ["DATABASE_URL"] = "sqlite:////opt/feature-factory/data/test.db"

def create_demo_task_with_rich_trace():
    """Создает демо задачу с богатыми trace событиями"""
    
    db_path = "/opt/feature-factory/data/test.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Создаем демо фичу если нет
        cursor.execute("""
            INSERT OR IGNORE INTO features 
            (id, title, status, priority, created_at, created_by, env, type) 
            VALUES (999, 'Демо фича для trace', 'DONE', 1, ?, 'Admin', 'TEST', 'INTERNAL')
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        
        # Создаем демо задачу
        cursor.execute("""
            INSERT OR REPLACE INTO tasks 
            (id, feature_id, role, dsl_json, status, attempts, scheduled_at, started_at) 
            VALUES (999, 999, 'Dev', '{"name": "Demo Trace Task"}', 'RUNNING', 1, ?, ?)
        """, (
            (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.now() - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        # Создаем богатые события для демонстрации
        base_time = datetime.now() - timedelta(minutes=20)
        
        events = [
            {
                "ts": base_time,
                "agent_role": "System",
                "task_id": "999",
                "event": "task_started",
                "details": {
                    "actor": "Admin",
                    "env": "TEST",
                    "correlation_id": "demo-trace-001"
                }
            },
            {
                "ts": base_time + timedelta(seconds=30),
                "agent_role": "Dev",
                "task_id": "999", 
                "event": "context_pack_built",
                "details": {
                    "pack_bytes": 15420,
                    "files_included": 12,
                    "correlation_id": "demo-trace-002"
                }
            },
            {
                "ts": base_time + timedelta(minutes=1),
                "agent_role": "Dev",
                "task_id": "999",
                "event": "llm_call_start", 
                "details": {
                    "model": "claude-3-sonnet",
                    "provider": "anthropic",
                    "role": "developer",
                    "correlation_id": "demo-trace-003"
                }
            },
            {
                "ts": base_time + timedelta(minutes=2),
                "agent_role": "Dev", 
                "task_id": "999",
                "event": "llm_call_end",
                "details": {
                    "model": "claude-3-sonnet",
                    "provider": "anthropic",
                    "input_tokens": 1500,
                    "output_tokens": 800,
                    "duration_ms": 3200,
                    "correlation_id": "demo-trace-004"
                }
            },
            {
                "ts": base_time + timedelta(minutes=3),
                "agent_role": "Dev",
                "task_id": "999",
                "event": "tool_edit",
                "details": {
                    "tool_name": "Edit",
                    "file_path": "/opt/feature-factory/app/demo.py",
                    "lines_changed": 15,
                    "correlation_id": "demo-trace-005",
                    "artifact_path": "/artifacts/demo.py"
                }
            },
            {
                "ts": base_time + timedelta(minutes=4),
                "agent_role": "QA",
                "task_id": "999",
                "event": "watchdog", 
                "details": {
                    "reason": "performance_check",
                    "threshold_ms": 5000,
                    "actual_ms": 4200,
                    "correlation_id": "demo-trace-006"
                }
            },
            {
                "ts": base_time + timedelta(minutes=5),
                "agent_role": "QA",
                "task_id": "999",
                "event": "tool_error",
                "details": {
                    "tool_name": "pytest",
                    "error_type": "TestFailure", 
                    "error_message": "Expected 200, got 404",
                    "correlation_id": "demo-trace-007"
                }
            },
            {
                "ts": base_time + timedelta(minutes=10),
                "agent_role": "Dev",
                "task_id": "999",
                "event": "done",
                "details": {
                    "status": "success",
                    "artifacts_created": 3,
                    "tests_passed": 15,
                    "correlation_id": "demo-trace-008"
                }
            }
        ]
        
        # Вставляем события
        for event in events:
            cursor.execute("""
                INSERT INTO agent_events (ts, agent_role, task_id, event, details_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event["ts"].strftime("%Y-%m-%d %H:%M:%S"),
                event["agent_role"],
                event["task_id"], 
                event["event"],
                json.dumps(event["details"])
            ))
        
        conn.commit()
        print(f"✅ Создана демо задача ID=999 с {len(events)} событиями")
        
        # Также обновим task_timeline_demo с более богатыми событиями
        rich_demo_events = [
            {
                "ts": base_time + timedelta(minutes=15),
                "agent_role": "Architect",
                "task_id": "task_timeline_demo",
                "event": "llm_call_start",
                "details": {
                    "model": "gpt-4",
                    "provider": "openai", 
                    "api_key": "sk-demo123456789",  # Будет отредактирован
                    "correlation_id": "demo-timeline-001"
                }
            },
            {
                "ts": base_time + timedelta(minutes=16),
                "agent_role": "Dev", 
                "task_id": "task_timeline_demo",
                "event": "tool_edit",
                "details": {
                    "tool_name": "Write",
                    "file_path": "/opt/feature-factory/demo_output.py",
                    "correlation_id": "demo-timeline-002",
                    "artifact_path": "/artifacts/demo_output.py"
                }
            },
            {
                "ts": base_time + timedelta(minutes=17),
                "agent_role": "QA",
                "task_id": "task_timeline_demo", 
                "event": "llm_error",
                "details": {
                    "error_type": "RateLimitError",
                    "error_message": "API rate limit exceeded",
                    "auth_token": "bearer_abc123",  # Будет отредактирован
                    "correlation_id": "demo-timeline-003"
                }
            }
        ]
        
        for event in rich_demo_events:
            cursor.execute("""
                INSERT INTO agent_events (ts, agent_role, task_id, event, details_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event["ts"].strftime("%Y-%m-%d %H:%M:%S"),
                event["agent_role"],
                event["task_id"],
                event["event"], 
                json.dumps(event["details"])
            ))
        
        conn.commit()
        print(f"✅ Добавлены богатые события для task_timeline_demo")

if __name__ == "__main__":
    create_demo_task_with_rich_trace()
    print("Демо данные созданы! Можно тестировать:")
    print("- Задача 999: http://127.0.0.1:8081/api/v1/tasks/999/trace")
    print("- task_timeline_demo: http://127.0.0.1:8081/api/v1/tasks/task_timeline_demo/trace")