#!/usr/bin/env python3
"""
API для получения информации о тасках и их execution trace.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Path, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id
# Импортируем сессию базы данных
from app.db.session import get_db

# Создаем роутер
router = APIRouter()


class TaskModel(BaseModel):
    id: int
    feature_id: int
    role: str
    status: str
    attempts: int
    budget_tokens: Optional[int] = None
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


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

def extract_description_and_links(details: Dict[str, Any], event_type: str) -> tuple[str, Dict[str, Any]]:
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

@router.get("/{task_id}/trace", response_model=TaskTraceResponse)
async def get_task_trace(
    request: Request,
    task_id: str = Path(..., description="ID таска для получения trace"),
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """
    Получает execution trace для указанного таска.
    
    Args:
        request: HTTP запрос
        task_id: ID таска
        limit: Максимальное количество событий (1-500)
        
    Returns:
        TaskTraceResponse: Список курируемых событий таска
    """
    start_time = time.time()
    request_correlation_id = generate_correlation_id()
    
    # Ограничиваем limit допустимыми значениями
    limit = max(1, min(limit, 500))
    
    log.info(
        event="task_trace_api_start",
        env=get_env(),
        component="tasks_api",
        agent_role="System",
        run_id=request_correlation_id,
        correlation_id=request_correlation_id,
        task_id=task_id,
        kv={
            "method": request.method,
            "url_path": str(request.url.path),
            "task_id": task_id,
            "limit": limit
        }
    )
    
    try:
        # Получаем события из базы данных
        query = text("""
            SELECT ts, agent_role, event, details_json
            FROM agent_events 
            WHERE task_id = :task_id 
            ORDER BY ts ASC 
            LIMIT :limit
        """)
        
        result = db.execute(query, {"task_id": task_id, "limit": limit})
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
        
        query_time = (time.time() - start_time) * 1000
        
        log.info(
            event="task_trace_api_success",
            env=get_env(),
            component="tasks_api",
            agent_role="System",
            run_id=request_correlation_id,
            correlation_id=request_correlation_id,
            task_id=task_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(query_time, 1),
                "task_id": task_id,
                "events_count": len(events)
            }
        )
        
        return response
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        
        log.error(
            event="task_trace_api_error",
            env=get_env(),
            component="tasks_api",
            agent_role="System",
            run_id=request_correlation_id,
            correlation_id=request_correlation_id,
            task_id=task_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(query_time, 1),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "task_id": task_id
            },
            stack=True
        )
        
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Failed to get task trace for {task_id}: {str(e)}",
            headers={
                "x-correlation-id": request_correlation_id,
                "error_code": "TASK_TRACE_API_ERROR"
            }
        )

@router.get("/{task_id}", response_model=TaskModel)
async def get_task(
    request: Request,
    task_id: int = Path(..., description="ID задачи"),
    db: Session = Depends(get_db)
):
    """
    Получает информацию о задаче по ID.
    """
    correlation_id = generate_correlation_id()
    
    try:
        query = text("""
            SELECT id, feature_id, role, status, attempts, budget_tokens, 
                   scheduled_at, started_at, finished_at
            FROM tasks 
            WHERE id = :task_id
        """)
        
        result = db.execute(query, {"task_id": task_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task = TaskModel(
            id=row.id,
            feature_id=row.feature_id,
            role=row.role,
            status=row.status,
            attempts=row.attempts or 0,
            budget_tokens=row.budget_tokens,
            scheduled_at=str(row.scheduled_at) if row.scheduled_at else None,
            started_at=str(row.started_at) if row.started_at else None,
            finished_at=str(row.finished_at) if row.finished_at else None
        )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(
            event="task_get_error",
            env=get_env(),
            component="tasks_api",
            agent_role="System",
            run_id=correlation_id,
            correlation_id=correlation_id,
            task_id=str(task_id),
            kv={"error_type": type(e).__name__, "error_message": str(e)}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task: {str(e)}",
            headers={"x-correlation-id": correlation_id}
        )