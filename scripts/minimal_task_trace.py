#!/usr/bin/env python3
"""
Минимальный тестовый файл для проверки работы API трассировки задач.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine, text

# Добавляем путь к проекту в sys.path
sys.path.append('/opt/feature-factory')

# Импортируем необходимые модули из проекта
from app.db.session import DATABASE_URL

class TraceEventModel:
    def __init__(self, timestamp: str, kind: str, icon: str, title: str, 
                 description: str, severity: str, links: Dict[str, Any], 
                 details: Dict[str, Any]):
        self.timestamp = timestamp
        self.kind = kind
        self.icon = icon
        self.title = title
        self.description = description
        self.severity = severity
        self.links = links
        self.details = details

class TaskTraceResponse:
    def __init__(self, task_id: str, items: List[TraceEventModel], total: int):
        self.task_id = task_id
        self.items = items
        self.total = total

# Маппинг событий -> иконки/заголовки/серьёзность
EVENT_MAPPINGS = {
    "task_started": {
        "icon": "🧠",
        "title": "Задача запущена",
        "severity": "info"
    },
    "context_pack_built": {
        "icon": "📦",
        "title": "Контекст собран",
        "severity": "info"
    },
    "llm_call_start": {
        "icon": "🤖",
        "title": "Вызов LLM начат",
        "severity": "info"
    },
    "llm_call_end": {
        "icon": "🤖",
        "title": "Вызов LLM завершён",
        "severity": "info"
    },
    "tool_apply": {
        "icon": "🔧",
        "title": "Применён инструмент",
        "severity": "info"
    },
    "watchdog_triggered": {
        "icon": "️⚠️",
        "title": "Codex: анти-зацикливание",
        "severity": "warn"
    },
    "qa_run_start": {
        "icon": "🧪",
        "title": "Тесты начаты",
        "severity": "info"
    },
    "qa_run_end_pass": {
        "icon": "✅",
        "title": "Тесты пройдены",
        "severity": "info"
    },
    "qa_run_end_fail": {
        "icon": "❌",
        "title": "Тесты провалены",
        "severity": "error"
    },
    "error": {
        "icon": "🔴",
        "title": "Ошибка",
        "severity": "error"
    },
    "exception": {
        "icon": "💥",
        "title": "Исключение",
        "severity": "error"
    },
    "task_done": {
        "icon": "✅",
        "title": "Задача завершена",
        "severity": "info"
    }
}

def normalize_event_type(event_type: str) -> str:
    """Нормализует тип события к snake_case."""
    # Простая нормализация - приводим к нижнему регистру
    return event_type.lower()

def get_event_mapping(event_type: str) -> Dict[str, Any]:
    """Получает маппинг для типа события."""
    normalized_type = normalize_event_type(event_type)
    mapping = EVENT_MAPPINGS.get(normalized_type, {
        "icon": "ℹ️",
        "title": f"Unknown({normalized_type})",
        "severity": "info"
    })
    return mapping

def extract_description_and_links(details: Dict[str, Any], event_type: str) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Извлекает описание и ссылки из деталей события."""
    description = ""
    links = {}
    
    # Извлекаем описание на основе типа события
    if event_type == "task_started":
        actor = details.get("actor", "Unknown")
        env = details.get("env", "Unknown")
        description = f"Инициатор: {actor}; контур: {env}"
    elif event_type == "context_pack_built":
        pack_bytes = details.get("pack_bytes", 0)
        description = f"Размер: {pack_bytes} bytes"
    elif event_type == "llm_call_start":
        model = details.get("model", "Unknown")
        provider = details.get("provider", "Unknown")
        role = details.get("role", "Unknown")
        description = f"Роль: {role}; модель: {model}; провайдер: {provider}"
    elif event_type == "llm_call_end":
        input_tokens = details.get("input_tokens", 0)
        output_tokens = details.get("output_tokens", 0)
        duration_ms = details.get("duration_ms", 0)
        description = f"Токены: {input_tokens} in / {output_tokens} out; время: {duration_ms} ms"
    elif event_type == "tool_apply":
        tool_name = details.get("tool_name", "Unknown")
        file_path = details.get("file_path", "Unknown")
        description = f"Инструмент: {tool_name}; файл: {file_path}"
    elif event_type == "watchdog_triggered":
        reason = details.get("reason", "Unknown")
        context = details.get("context", "Unknown")
        description = f"Причина: {reason}; контекст: {context}"
    elif event_type == "qa_run_start":
        test_suite = details.get("test_suite", "Unknown")
        description = f"Запущен тестовый набор: {test_suite}"
    elif event_type == "qa_run_end_pass":
        passed = details.get("passed", 0)
        description = f"Пройдено тестов: {passed}"
    elif event_type == "qa_run_end_fail":
        failed = details.get("failed", 0)
        passed = details.get("passed", 0)
        test_name = details.get("test_name", "Unknown")
        description = f"Провалено тестов: {failed}; пройдено: {passed}; тест: {test_name}"
    elif event_type == "task_done":
        status = details.get("status", "Unknown")
        description = f"Статус: {status}"
    elif event_type in ["error", "exception"]:
        error_type = details.get("error_type", "Unknown")
        description = f"Тип ошибки: {error_type}"
    else:
        # Для неизвестных типов событий используем общее описание
        description = f"Событие типа: {event_type}"
    
    # Извлекаем ссылки
    if "correlation_id" in details:
        links["log_id"] = details["correlation_id"]
    
    if "artifact_path" in details:
        links["artifact"] = details["artifact_path"]
    
    # Удаляем секреты из деталей
    redacted_details = {}
    for key, value in details.items():
        # Проверяем, не является ли ключ секретом
        if any(secret_word in key.lower() for secret_word in ["token", "secret", "password", "key"]):
            redacted_details[key] = "***REDACTED***"
        else:
            redacted_details[key] = value
    
    return description, links, redacted_details

def get_task_trace(task_id: str, limit: int = 200) -> TaskTraceResponse:
    """
    Получает execution trace для указанного таска.
    
    Args:
        task_id: ID таска
        limit: Максимальное количество событий (1-500)
        
    Returns:
        TaskTraceResponse: Список курируемых событий таска
    """
    # Ограничиваем limit допустимыми значениями
    limit = max(1, min(limit, 500))
    
    # Создаем подключение к базе данных
    engine = create_engine(DATABASE_URL)
    
    # Получаем события из базы данных
    with engine.connect() as conn:
        query = text("""
            SELECT ts, agent_role, event, details_json
            FROM agent_events 
            WHERE task_id = :task_id 
            ORDER BY ts ASC 
            LIMIT :limit
        """)
        
        result = conn.execute(query, {"task_id": task_id, "limit": limit})
        rows = result.fetchall()
        
        events = []
        for row in rows:
            ts, agent_role, event_type, details_json = row
            
            # Парсим JSON с деталями
            try:
                details = json.loads(details_json) if details_json else {}
            except json.JSONDecodeError:
                details = {}
            
            # Получаем маппинг для события
            mapping = get_event_mapping(event_type)
            
            # Извлекаем описание и ссылки
            description, links, redacted_details = extract_description_and_links(details, event_type)
            
            # Создаем событие
            event = TraceEventModel(
                timestamp=ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                kind=normalize_event_type(event_type),
                icon=mapping["icon"],
                title=mapping["title"],
                description=description,
                severity=mapping["severity"],
                links=links,
                details=redacted_details
            )
            events.append(event)
    
    response = TaskTraceResponse(
        task_id=task_id,
        items=events,
        total=len(events)
    )
    
    return response

def main():
    """Основная функция для тестирования."""
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
    else:
        task_id = "task-119"
    
    try:
        response = get_task_trace(task_id)
        print(f"Task ID: {response.task_id}")
        print(f"Total events: {response.total}")
        print("\nEvents:")
        for i, event in enumerate(response.items):
            print(f"  {i+1}. {event.timestamp} - {event.title}")
            print(f"     Description: {event.description}")
            print(f"     Severity: {event.severity}")
            print(f"     Links: {event.links}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()