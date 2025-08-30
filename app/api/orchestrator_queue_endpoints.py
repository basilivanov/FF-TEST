#!/usr/bin/env python3
"""
Эндпоинты для получения очередей фич и задач.
"""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
import time
import uuid
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.api.schemas.orchestrator_schemas import TaskPlanResponse, ErrorResponse
from app.logging_helpers import log, get_env, generate_correlation_id
from app.db.session import get_db
from app.utils.datetime_helpers import serialize_datetime_safe


# Создаем роутер
router = APIRouter(prefix="/api/v1/orchestrator")

# Pydantic модели для ответов
class QueuedFeatureResponse(BaseModel):
    """Схема фичи в очереди."""
    id: int
    title: str
    status: str
    priority: int
    created_at: str
    created_by: str
    env: str
    scheduled_at: Optional[str] = None

class QueuedTaskResponse(BaseModel):
    """Схема задачи в очереди."""
    id: int
    feature_id: int
    feature_title: str
    role: str
    status: str
    attempts: int
    scheduled_at: str
    budget_tokens: Optional[int] = None

class RunningTaskResponse(BaseModel):
    """Схема запущенной задачи."""
    id: int
    feature_id: int
    feature_title: str
    role: str
    started_at: str
    elapsed_ms: int


@router.get("/features/queue",
             response_model=List[QueuedFeatureResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def get_queued_features(request: Request):
    """
    Получить список фич в очереди.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[QueuedFeatureResponse]: Список фич в очереди
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()
    
    # Логируем начало вызова
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "endpoint": "GET /orchestrator/features/queue"
        }
    )
    
    try:
        # Получаем сессию базы данных
        db_gen = get_db()
        db = next(db_gen)
        
        # Получаем фичи со статусом NEW или PLANNED из базы данных
        result = db.execute(
            text("""
                SELECT id, title, status, priority, 
                       REPLACE(created_at, ' ', 'T') || 'Z' as created_at, 
                       created_by, env, 
                       REPLACE(COALESCE(scheduled_at, created_at), ' ', 'T') || 'Z' as scheduled_at
                FROM features 
                WHERE status IN ('NEW', 'PLANNED')
                ORDER BY priority DESC, created_at ASC
                LIMIT 100
            """)
        )
        
        queued_features = []
        for row in result:
            # Даты уже преобразованы в SQL запросе
            created_at_str = row[4] or ""
            scheduled_at_str = row[7] or ""
                    
            queued_features.append(
                QueuedFeatureResponse(
                    id=row[0],
                    title=row[1],
                    status=row[2],
                    priority=row[3] or 0,  # Устанавливаем priority=0 по умолчанию
                    created_at=created_at_str,
                    created_by=row[5] or "system",  # По умолчанию "system"
                    env=row[6] or "test",  # По умолчанию "test"
                    scheduled_at=scheduled_at_str
                )
            )
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "features_count": len(queued_features)
            }
        )
        
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        return queued_features
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        except:
            pass
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get queued features: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/tasks/queue",
             response_model=List[QueuedTaskResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def get_queued_tasks(request: Request):
    """
    Получить список задач в очереди.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[QueuedTaskResponse]: Список задач в очереди
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()
    
    # Логируем начало вызова
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "endpoint": "GET /orchestrator/tasks/queue"
        }
    )
    
    try:
        # Получаем сессию базы данных
        db_gen = get_db()
        db = next(db_gen)
        
        # Получаем задачи со статусом NEW или WAIT_BUDGET из базы данных
        result = db.execute(
            text("""
                SELECT t.id, t.feature_id, f.title, t.role, t.status, t.attempts, 
                       REPLACE(t.scheduled_at, ' ', 'T') || 'Z' as scheduled_at, t.budget_tokens
                FROM tasks t
                JOIN features f ON t.feature_id = f.id
                WHERE t.status IN ('NEW', 'WAIT_BUDGET')
                ORDER BY t.scheduled_at ASC
                LIMIT 100
            """)
        )
        
        queued_tasks = []
        for row in result:
            # Даты уже преобразованы в SQL запросе
            scheduled_at_str = row[6] or ""
                    
            queued_tasks.append(
                QueuedTaskResponse(
                    id=row[0],
                    feature_id=row[1],
                    feature_title=row[2],
                    role=row[3],
                    status=row[4],
                    attempts=row[5] or 0,  # По умолчанию 0 попыток
                    scheduled_at=scheduled_at_str,
                    budget_tokens=row[7]
                )
            )
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "tasks_count": len(queued_tasks)
            }
        )
        
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        return queued_tasks
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        except:
            pass
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get queued tasks: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/tasks/running",
             response_model=List[RunningTaskResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def get_running_tasks(request: Request):
    """
    Получить список запущенных задач.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[RunningTaskResponse]: Список запущенных задач
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()
    
    # Логируем начало вызова
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Orchestrator",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "endpoint": "GET /orchestrator/tasks/running"
        }
    )
    
    try:
        # Получаем сессию базы данных
        db_gen = get_db()
        db = next(db_gen)
        
        # Получаем задачи со статусом RUNNING из базы данных
        # Также получаем время начала задачи из started_at
        result = db.execute(
            text("""
                SELECT t.id, t.feature_id, f.title, t.role, 
                       REPLACE(t.started_at, ' ', 'T') || 'Z' as started_at
                FROM tasks t
                JOIN features f ON t.feature_id = f.id
                WHERE t.status = 'RUNNING'
                ORDER BY t.started_at DESC
                LIMIT 50
            """)
        )
        
        running_tasks = []
        current_time = time.time()
        
        for row in result:
            # Даты уже преобразованы в SQL запросе, вычисляем elapsed_ms
            started_at_str = row[4] or ""
            elapsed_ms = 0
            # Для вычисления elapsed нужно распарсить дату обратно
            if row[4]:
                try:
                    from datetime import datetime
                    # Парсим дату в формате ISO с Z
                    dt = datetime.fromisoformat(row[4].replace('Z', '+00:00'))
                    started_at_timestamp = dt.timestamp()
                    elapsed_ms = int((current_time - started_at_timestamp) * 1000)
                except:
                    elapsed_ms = 0
                    
            running_tasks.append(
                RunningTaskResponse(
                    id=row[0],
                    feature_id=row[1],
                    feature_title=row[2],
                    role=row[3],
                    started_at=started_at_str,
                    elapsed_ms=elapsed_ms
                )
            )
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "tasks_count": len(running_tasks)
            }
        )
        
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        return running_tasks
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Orchestrator",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        except:
            pass
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get running tasks: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )