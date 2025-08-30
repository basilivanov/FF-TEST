
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Path, Query, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.logging_helpers import log, get_env, generate_correlation_id
from app.db.session import get_db

router = APIRouter()

class TraceEventModel(BaseModel):
    timestamp: str
    kind: str
    icon: str
    title: str
    description: str
    severity: str
    links: Dict[str, Any]
    details: Dict[str, Any]

class TaskTraceResponse(BaseModel):
    task_id: str
    items: List[TraceEventModel]
    total: int

EVENT_MAPPINGS = {
    "task_started": {"icon": "🧠", "title": "Задача запущена", "severity": "info"},
    "context_pack_built": {"icon": "📦", "title": "Контекст собран", "severity": "info"},
    "llm_call_start": {"icon": "🤖", "title": "Вызов LLM начат", "severity": "info"},
    "llm_call_end": {"icon": "🤖", "title": "Вызов LLM завершён", "severity": "info"},
    "tool_edit": {"icon": "🔧", "title": "Инструмент редактирования", "severity": "info"},
    "watchdog": {"icon": "🛡️", "title": "Сторожевой таймер", "severity": "warn"},
    "done": {"icon": "✅", "title": "Завершено", "severity": "info"},
    "tool_error": {"icon": "🔴", "title": "Ошибка инструмента", "severity": "error"},
    "llm_error": {"icon": "🔴", "title": "Ошибка LLM", "severity": "error"}
}

def get_event_mapping(event_type: str) -> Dict[str, Any]:
    """Получает маппинг для типа события."""
    return EVENT_MAPPINGS.get(event_type, {
        "icon": "ℹ️",
        "title": f"Неизвестное({event_type})",
        "severity": "info"
    })

def redact_secrets(details: Dict[str, Any]) -> Dict[str, Any]:
    """Редактирует секреты в деталях события."""
    redacted = {}
    secret_keywords = ["token", "password", "key", "secret", "auth", "credential"]
    safe_keywords = ["correlation_id", "log_id", "task_id", "run_id"]
    
    for key, value in details.items():
        # Пропускаем безопасные ключи
        if any(safe_key in key.lower() for safe_key in safe_keywords):
            redacted[key] = value
        elif any(keyword in key.lower() for keyword in secret_keywords):
            redacted[key] = "***REDACTED***"
        elif isinstance(value, str) and any(keyword in value.lower() for keyword in secret_keywords):
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    
    return redacted

def extract_description_and_links(details: Dict[str, Any], event_type: str) -> tuple[str, Dict[str, Any]]:
    """Извлекает описание и ссылки из деталей события."""
    description = ""
    links = {}
    
    if event_type == "task_started":
        actor = details.get("actor", "Unknown")
        description = f"Инициатор: {actor}"
    elif event_type == "context_pack_built":
        pack_size = details.get("pack_bytes", details.get("size", 0))
        description = f"Размер: {pack_size} bytes"
    elif event_type in ["llm_call_start", "llm_call_end"]:
        model = details.get("model", "Unknown")
        provider = details.get("provider", "Unknown")
        description = f"Модель: {model}, Провайдер: {provider}"
    elif event_type == "tool_edit":
        tool_name = details.get("tool_name", "Edit")
        file_path = details.get("file_path", "")
        description = f"Инструмент: {tool_name}, Файл: {file_path}"
    elif event_type == "watchdog":
        reason = details.get("reason", "timeout")
        description = f"Причина: {reason}"
    elif event_type in ["tool_error", "llm_error"]:
        error_type = details.get("error_type", "Unknown")
        description = f"Ошибка: {error_type}"
    else:
        description = f"Событие: {event_type}"
    
    if "artifact_path" in details:
        links["artifact"] = details["artifact_path"]
    
    return description, links

@router.get("/tasks/{task_id}/trace", response_model=TaskTraceResponse)
async def get_task_trace(
    request: Request,
    task_id: str = Path(..., description="ID задачи для получения trace"),
    limit: int = Query(50, ge=1, le=100, description="Количество событий"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: Session = Depends(get_db)
):
    """
    Получает execution trace для указанной задачи.
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()
    
    log.info(
        event="task_trace_request",
        env=get_env(),
        component="trace_api",
        agent_role="System",
        run_id=correlation_id,
        correlation_id=correlation_id,
        task_id=task_id,
        kv={"task_id": task_id, "limit": limit, "offset": offset}
    )
    
    try:
        query = text("""
            SELECT ts, agent_role, event, details_json
            FROM agent_events 
            WHERE task_id = :task_id 
            ORDER BY ts DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"task_id": task_id, "limit": limit, "offset": offset})
        rows = result.fetchall()
        
        events = []
        for row in rows:
            ts, agent_role, event_type, details_json = row
            
            try:
                details = json.loads(details_json) if details_json else {}
            except json.JSONDecodeError:
                details = {}
            
            mapping = get_event_mapping(event_type)
            description, links = extract_description_and_links(details, event_type)
            
            links["log_id"] = correlation_id
            
            event = TraceEventModel(
                timestamp=ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                kind=event_type,
                icon=mapping["icon"],
                title=mapping["title"],
                description=description,
                severity=mapping["severity"],
                links=links,
                details=redact_secrets(details)
            )
            events.append(event)
        
        response = TaskTraceResponse(task_id=task_id, items=events, total=len(events))
        
        duration_ms = round((time.time() - start_time) * 1000, 1)
        
        log.info(
            event="task_trace_success",
            env=get_env(),
            component="trace_api", 
            agent_role="System",
            run_id=correlation_id,
            correlation_id=correlation_id,
            task_id=task_id,
            kv={"duration_ms": duration_ms, "events_count": len(events), "status": 200}
        )
        
        return response
        
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 1)
        
        log.error(
            event="task_trace_error",
            env=get_env(),
            component="trace_api",
            agent_role="System", 
            run_id=correlation_id,
            correlation_id=correlation_id,
            task_id=task_id,
            kv={"duration_ms": duration_ms, "error_type": type(e).__name__, "error_message": str(e), "status": 500}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task trace: {str(e)}",
            headers={"x-correlation-id": correlation_id}
        )

