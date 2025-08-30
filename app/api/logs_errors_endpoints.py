#!/usr/bin/env python3
"""
Эндпоинты для получения ошибок из логов.
"""

import json
import time
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, Request
from sqlalchemy import create_engine, text

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Создаем роутер
router = APIRouter(prefix="/api/v1/logs")


@router.get("/errors")
async def get_error_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Количество записей для получения"),
    level: Optional[str] = Query(None, description="Фильтр по уровню лога (ERROR, WARNING, CRITICAL)"),
    component: Optional[str] = Query(None, description="Фильтр по компоненту"),
    agent_role: Optional[str] = Query(None, description="Фильтр по роли агента")
):
    """
    Получает последние записи логов с уровнями ERROR, WARNING, CRITICAL.
    
    Args:
        request: HTTP запрос
        limit: Количество записей для получения (по умолчанию 100)
        level: Фильтр по уровню лога (ERROR, WARNING, CRITICAL)
        component: Фильтр по компоненту
        agent_role: Фильтр по роли агента
        
    Returns:
        List[Dict[str, Any]]: Список записей логов с ошибками
    """
    # Генерируем correlation_id
    correlation_id = generate_correlation_id()
    
    # Логируем начало вызова
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="System",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "limit": limit,
            "level": level,
            "component": component,
            "agent_role": agent_role
        }
    )
    
    try:
        # Получаем DATABASE_URL из переменных окружения
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
        engine = create_engine(DATABASE_URL)
        
        # Формируем запрос с фильтрацией по уровням ошибок
        query_parts = ["SELECT * FROM agent_events WHERE level IN ('ERROR', 'WARNING', 'CRITICAL')"]
        params = {}
        
        # Добавляем фильтр по уровню, если указан
        if level:
            query_parts.append("AND level = :level")
            params["level"] = level
            
        # Добавляем фильтр по компоненту, если указан
        if component:
            query_parts.append("AND component = :component")
            params["component"] = component
            
        # Добавляем фильтр по роли агента, если указана
        if agent_role:
            query_parts.append("AND agent_role = :agent_role")
            params["agent_role"] = agent_role
            
        # Добавляем сортировку и лимит
        query_parts.append("ORDER BY ts DESC LIMIT :limit")
        params["limit"] = limit
        
        # Собираем полный запрос
        query = " ".join(query_parts)
        
        # Выполняем запрос
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
        # Преобразуем результаты в список словарей
        error_logs = []
        for row in rows:
            # Преобразуем Row в словарь
            row_dict = {
                "id": row[0],
                "ts": row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1]),
                "agent_role": row[2],
                "task_id": row[3],
                "event": row[4],
                "details_json": row[5]
            }
            
            # Парсим details_json если это возможно
            try:
                details = json.loads(row[5]) if row[5] else {}
                row_dict.update(details)
            except json.JSONDecodeError:
                # Если не удалось распарсить, оставляем details_json как есть
                row_dict["details_json"] = row[5]
                
            error_logs.append(row_dict)
        
        # Логируем успешное завершение вызова
        log.info(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="System",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": 10,  # TODO: Calculate real duration
                "records_returned": len(error_logs)
            }
        )
        
        return error_logs
        
    except Exception as e:
        # Логируем ошибку
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="System",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": 10,  # TODO: Calculate real duration
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get error logs: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )