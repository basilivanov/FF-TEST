#!/usr/bin/env python3
"""
Скрипт для генерации тестовых данных в таблице agent_events.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Добавляем путь к проекту в sys.path
sys.path.append('/opt/feature-factory')

# Импортируем необходимые модули из проекта
from app.db.session import DATABASE_URL

def generate_test_events(task_id: str = "task-119", count: int = 8):
    """Генерирует тестовые события для задачи."""
    
    # Создаем подключение к базе данных
    engine = create_engine(DATABASE_URL)
    
    # Получаем текущее время
    now = datetime.now()
    
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
    for i in range(min(count, len(event_types))):
        event_time = now - timedelta(minutes=count-i)
        event_data = event_types[i].copy()
        event_data["ts"] = event_time
        events.append(event_data)
    
    # Добавляем дополнительные события, если count больше, чем количество типов событий
    if count > len(event_types):
        for i in range(len(event_types), count):
            event_time = now - timedelta(minutes=count-i)
            event_data = {
                "event": f"custom_event_{i}",
                "agent_role": "Dev",
                "ts": event_time,
                "details": {
                    "description": f"Custom event {i}",
                    "value": i * 10
                }
            }
            events.append(event_data)
    
    # Вставляем события в базу данных
    with engine.connect() as conn:
        for event in events:
            # Генерируем уникальный correlation_id для каждого события
            correlation_id = f"corr-{uuid.uuid4().hex[:8]}"
            
            # Добавляем correlation_id в details
            details = event["details"].copy()
            details["correlation_id"] = correlation_id
            
            # Если это событие с артефактом, добавляем путь к артефакту
            if event["event"] in ["context_pack_built", "tool_apply"]:
                details["artifact_path"] = f"/artifacts/{task_id}/{event['event']}.json"
            
            # Подготавливаем SQL-запрос
            query = text("""
                INSERT INTO agent_events (ts, agent_role, task_id, event, details_json)
                VALUES (:ts, :agent_role, :task_id, :event, :details_json)
            """)
            
            # Выполняем запрос
            conn.execute(query, {
                "ts": event["ts"],
                "agent_role": event["agent_role"],
                "task_id": task_id,
                "event": event["event"],
                "details_json": str(details).replace("'", "\"")
            })
        
        # Коммитим изменения
        conn.commit()
    
    print(f"Сгенерировано {len(events)} тестовых событий для задачи {task_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        generate_test_events(task_id, count)
    else:
        generate_test_events()
