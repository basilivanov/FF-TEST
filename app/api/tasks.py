#!/usr/bin/env python3
"""
API для получения информации о задачах.
"""

from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Path, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.logging_helpers import log, get_env, generate_correlation_id
from app.db.session import get_db

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