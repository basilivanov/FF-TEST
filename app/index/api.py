from fastapi import APIRouter, HTTPException, Request, Query
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from pydantic import BaseModel
from app.logging_helpers import log_job, log_db, log_http, get_env
from app.api.middleware import get_correlation_id, get_env_from_scope
from app.index.service import get_index_service
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import structlog

# Настройка логгера
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/index")

class CallGraphEdge(BaseModel):
    id: int
    source_symbol: str
    target_symbol: str
    file_path: str
    line_number: int

class CallGraphResponse(BaseModel):
    edges: List[CallGraphEdge]
    total: int
    limit: int
    offset: int
    as_of: str
    stale: bool

def get_database_url():
    """Получает URL базы данных из переменной окружения или использует тестовую базу."""
    return os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/index.db")

@router.get("/symbol")
def get_symbol(request: Request, symbol_name: str = None, file_path: str = None):
    """Получает информацию о символах из индекса."""
    # Получаем correlation_id из запроса
    correlation_id = get_correlation_id(request)
    env = get_env_from_scope(request)
    
    # Логируем начало запроса
    log.info(
        event="api_call_start",
        env=env,
        component="api",
        agent_role="Dev",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": "GET",
            "url_host": "localhost",
            "url_path": "/api/v1/index/symbol",
            "symbol_name": symbol_name,
            "file_path": file_path
        }
    )
    
    start_time = time.time()
    
    try:
        # Используем IndexService
        index_service = get_index_service()
        symbols = index_service.get_symbol(symbol_name=symbol_name, file_path=file_path)
        
        # Логируем успешное завершение запроса
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=env,
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": "localhost",
                "url_path": "/api/v1/index/symbol",
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "symbols_count": len(symbols)
            }
        )
        
        return {"symbols": symbols}
    except Exception as e:
        # Логируем ошибку
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=env,
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": "localhost",
                "url_path": "/api/v1/index/symbol",
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {e}")

@router.get("/calls", response_model=CallGraphResponse)
def get_calls(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Количество ребер"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    source_symbol: str = Query(None, description="Фильтр по исходному символу"),
    target_symbol: str = Query(None, description="Фильтр по целевому символу"), 
    file_path: str = Query(None, description="Фильтр по файлу"),
    db: Session = Depends(get_db)
):
    """Получает информацию о вызовах из графа вызовов."""
    correlation_id = get_correlation_id(request)
    env = get_env_from_scope(request)
    
    log.info(
        event="api_call_start",
        env=env,
        component="index_api",
        agent_role="Dev",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": "GET",
            "url_path": "/api/v1/index/calls",
            "limit": limit,
            "offset": offset,
            "source_symbol": source_symbol,
            "target_symbol": target_symbol,
            "file_path": file_path
        }
    )
    
    start_time = time.time()
    
    try:
        # Строим WHERE условия
        conditions = []
        params = {}
        
        if source_symbol:
            conditions.append("source_symbol = :source_symbol")
            params["source_symbol"] = source_symbol
        if target_symbol:
            conditions.append("target_symbol = :target_symbol") 
            params["target_symbol"] = target_symbol
        if file_path:
            conditions.append("file_path = :file_path")
            params["file_path"] = file_path
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Получаем общее количество
        count_query = f"SELECT COUNT(*) FROM call_graph_edges{where_clause}"
        total_result = db.execute(text(count_query), params)
        total = total_result.scalar() or 0
        
        # Получаем ребра с пагинацией
        edges_query = f"SELECT id, source_symbol, target_symbol, file_path, line_number FROM call_graph_edges{where_clause} LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})
        
        edges_result = db.execute(text(edges_query), params)
        edges = []
        
        for row in edges_result:
            edges.append(CallGraphEdge(
                id=row.id,
                source_symbol=row.source_symbol,
                target_symbol=row.target_symbol,
                file_path=row.file_path,
                line_number=row.line_number
            ))
        
        # Проверяем актуальность данных (простая проверка)
        stale = total == 0
        as_of = datetime.now(timezone.utc).isoformat()
        
        response = CallGraphResponse(
            edges=edges,
            total=total,
            limit=limit,
            offset=offset,
            as_of=as_of,
            stale=stale
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=env,
            component="index_api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_path": "/api/v1/index/calls",
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "total": total,
                "edges_count": len(edges),
                "stale": stale
            }
        )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=env,
            component="index_api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_path": "/api/v1/index/calls",
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        
        # Возвращаем управляемый ответ при ошибке (defensive)
        return CallGraphResponse(
            edges=[],
            total=0,
            limit=limit,
            offset=offset,
            as_of=datetime.now(timezone.utc).isoformat(),
            stale=True
        )

@router.get("/module-card")
def get_module_card(request: Request, file_path: str):
    """Получает карточку модуля."""
    # Получаем correlation_id из запроса
    correlation_id = get_correlation_id(request)
    env = get_env_from_scope(request)
    
    # Логируем начало запроса
    log.info(
        event="api_call_start",
        env=env,
        component="api",
        agent_role="Dev",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": "GET",
            "url_host": "localhost",
            "url_path": "/api/v1/index/module-card",
            "file_path": file_path
        }
    )
    
    start_time = time.time()
    
    try:
        # Используем IndexService
        index_service = get_index_service()
        module_card = index_service.get_module_card(file_path=file_path)
        
        # Логируем успешное завершение запроса
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=env,
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": "localhost",
                "url_path": "/api/v1/index/module-card",
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "file_path": file_path
            }
        )
        
        return {"module_card": module_card}
    except Exception as e:
        # Логируем ошибку
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=env,
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": "localhost",
                "url_path": "/api/v1/index/module-card",
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=f"Ошибка сервиса: {e}")