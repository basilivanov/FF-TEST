from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
import time
import uuid
import os
from typing import List
from app.api.schemas.orchestrator_schemas import TaskPlanResponse, ErrorResponse, GraphStatusResponse
from app.logging_helpers import log, get_env, generate_correlation_id
from app.db.session import get_db
from app.utils.datetime_helpers import serialize_datetime_safe

# Создаем роутер
router = APIRouter(prefix="/api/v1/orchestrator")


@router.get("/tasks",
             response_model=List[TaskPlanResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def list_tasks(request: Request):
    """
    Получить список всех задач.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[TaskPlanResponse]: Список задач
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
            "endpoint": "GET /orchestrator/tasks"
        }
    )
    
    try:
        # Получаем сессию базы данных
        db_gen = get_db()
        db = next(db_gen)
        
        # Получаем задачи из базы данных
        result = db.execute(
            text("SELECT id, feature_id, role, status FROM tasks")
        )
        
        tasks = []
        for row in result:
            tasks.append(
                TaskPlanResponse(
                    id=row[0],
                    role=row[2],
                    status=row[3]
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
                "tasks_count": len(tasks)
            }
        )
        
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        return tasks
        
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
            detail=f"Failed to list tasks: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )


@router.get("/runs",
             response_model=List[GraphStatusResponse],
             responses={
                 500: {"model": ErrorResponse}
             })
async def list_runs(request: Request):
    """
    Получить список всех запусков графов.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[GraphStatusResponse]: Список запусков графов
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
            "endpoint": "GET /orchestrator/runs"
        }
    )
    
    try:
        # Получаем сессию базы данных
        db_gen = get_db()
        db = next(db_gen)
        
        # Получаем запуски графов из базы данных
        result = db.execute(
            text("""
                SELECT run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at 
                FROM graph_runs
                ORDER BY last_checkpoint_at DESC
                LIMIT 100
            """)
        )
        
        runs = []
        for row in result:
            # Преобразуем datetime в UTC ISO строку с 'Z'
            last_checkpoint = serialize_datetime_safe(row[6])
                    
            runs.append(
                GraphStatusResponse(
                    run_id=row[0],
                    graph=row[2] or "G1",
                    status=row[5] or "UNKNOWN",
                    feature_status="UNKNOWN", # TODO: Получить статус фичи
                    last_checkpoint=last_checkpoint,
                    env=get_env()
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
                "runs_count": len(runs)
            }
        )
        
        # Закрываем сессию
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        return runs
        
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
            detail=f"Failed to list runs: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )