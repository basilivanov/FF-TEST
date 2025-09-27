#!/usr/bin/env python3
"""
Admin routes for Feature Factory.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from app.logging_helpers import log_http
from app.admin.auth import ensure_admin_credentials
from app.api.llm_status import llm_status as get_llm_status
import structlog

# Настройка логгера
log = structlog.get_logger()

# Security
security = HTTPBasic()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(prefix="/admin")

def get_env() -> str:
    """Get current environment."""
    return os.getenv("ENV", "test")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic auth credentials using shared admin auth helpers."""
    return ensure_admin_credentials(credentials)

@router.get("/")
def admin_root():
    """Admin panel root."""
    return {
        "message": "Feature Factory Admin Panel",
        "endpoints": {
            "jobs": "/admin/jobs",
            "logs": "/admin/logs", 
            "tokens": "/admin/tokens",
            "call-graph": "/admin/call-graph",
            "sqladmin": "/admin/sqladmin/",
            "llm-providers-status": "/admin/llm/providers-status"
        }
    }

@router.get("/llm/providers-status")
@log_http
def admin_llm_providers_status(request: Request, username: str = Depends(get_current_username)):
    """LLM providers status with detailed auth/CLI probe info."""
    correlation_id = request.headers.get("x-correlation-id", "unknown")
    try:
        status_payload = get_llm_status()
        log.info(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_llm_status",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/llm/providers-status",
                "status": 200,
                "providers": len(status_payload.get("providers", []))
            }
        )
        return status_payload
    except Exception as e:
        log.error(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_llm_status",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/llm/providers-status",
                "status": 500,
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs")
@log_http
def get_jobs(request: Request, username: str = Depends(get_current_username)):
    """Get list of jobs."""
    correlation_id = request.headers.get("x-correlation-id", "unknown")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM jobs ORDER BY id DESC LIMIT 100"))
            jobs = []
            for row in result:
                jobs.append({
                    "id": row[0],
                    "name": row[1],
                    "params_json": row[2],
                    "status": row[3],
                    "started_at": row[4],
                    "finished_at": row[5],
                    "result_json": row[6],
                    "retries": row[7]
                })
        
        log.info(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_jobs",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/jobs",
                "status": 200,
                "jobs_count": len(jobs)
            }
        )
        
        return {"jobs": jobs}
    except Exception as e:
        log.error(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_jobs",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/jobs",
                "status": 500,
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
@log_http
def get_logs(request: Request, 
             component: str = None, 
             level: str = None, 
             event: str = None,
             username: str = Depends(get_current_username)):
    """Get logs with optional filters."""
    correlation_id = request.headers.get("x-correlation-id", "unknown")
    
    try:
        with engine.connect() as conn:
            # Build query with filters
            query = "SELECT * FROM agent_events WHERE 1=1"
            params = {}
            
            if component:
                query += " AND agent_role = :component"
                params["component"] = component
            
            if level:
                # В agent_events у нас нет level, но можно фильтровать по event
                query += " AND event = :event"
                params["event"] = event or level
            
            if event:
                query += " AND event = :event"
                params["event"] = event
            
            query += " ORDER BY ts DESC LIMIT 100"
            
            result = conn.execute(text(query), params)
            logs = []
            for row in result:
                logs.append({
                    "id": row[0],
                    "ts": row[1],
                    "agent_role": row[2],
                    "task_id": row[3],
                    "event": row[4],
                    "details_json": row[5]
                })
        
        log.info(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_logs",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/logs",
                "status": 200,
                "logs_count": len(logs)
            }
        )
        
        return {"logs": logs}
    except Exception as e:
        log.error(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_logs",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/logs",
                "status": 500,
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens")
@log_http
def get_token_stats(request: Request, 
                   date: str = None,
                   username: str = Depends(get_current_username)):
    """Get token statistics."""
    correlation_id = request.headers.get("x-correlation-id", "unknown")
    
    try:
        from app.llm.token_stats import get_token_stats
        token_stats = get_token_stats()
        
        # Парсим дату если указана
        from datetime import datetime, date as dt_date
        target_date = None
        if date:
            try:
                target_date = dt_date.fromisoformat(date)
            except ValueError:
                target_date = None
        
        # Получаем статистику
        stats = token_stats.get_daily_stats(target_date)
        
        log.info(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_tokens",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/tokens",
                "status": 200,
                "tokens_stats_count": len(stats)
            }
        )
        
        return {"token_stats": stats}
    except Exception as e:
        log.error(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_tokens",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/tokens",
                "status": 500,
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call-graph")
@log_http
def get_call_graph(request: Request,
                   module_filter: str = None,
                   max_nodes: int = 100,
                   username: str = Depends(get_current_username)):
    """Get call graph data for visualization."""
    correlation_id = request.headers.get("x-correlation-id", "unknown")
    
    try:
        with engine.connect() as conn:
            # Получаем топ модули по количеству вызовов
            top_modules_query = """
                SELECT source_symbol, COUNT(*) as outgoing_calls
                FROM call_graph_edges 
                WHERE source_symbol LIKE '%app.%'
                GROUP BY source_symbol
                ORDER BY outgoing_calls DESC
                LIMIT :max_nodes
            """
            
            result = conn.execute(text(top_modules_query), {"max_nodes": max_nodes})
            top_modules = [row[0] for row in result]
            
            if not top_modules:
                return {"nodes": [], "links": [], "stats": {"total_nodes": 0, "total_edges": 0}}
            
            # Получаем связи между топ модулями
            placeholders = ','.join([f':module_{i}' for i in range(len(top_modules))])
            params = {f'module_{i}': module for i, module in enumerate(top_modules)}
            
            links_query = f"""
                SELECT source_symbol, target_symbol, COUNT(*) as weight, file_path
                FROM call_graph_edges
                WHERE source_symbol IN ({placeholders})
                   OR target_symbol IN ({placeholders})
                GROUP BY source_symbol, target_symbol, file_path
                ORDER BY weight DESC
                LIMIT 500
            """
            
            result = conn.execute(text(links_query), params)
            links = []
            all_symbols = set()
            
            for row in result:
                source, target, weight, file_path = row
                # Упрощаем имена модулей для визуализации
                source_short = source.split('.')[-2:] if '.' in source else [source]
                target_short = target.split('.')[-2:] if '.' in target else [target]
                
                source_name = '.'.join(source_short[-2:])
                target_name = '.'.join(target_short[-2:])
                
                if source_name != target_name:  # Избегаем self-loops
                    links.append({
                        "source": source_name,
                        "target": target_name,
                        "weight": weight,
                        "file_path": file_path.split('/')[-1] if file_path else "",
                        "full_source": source,
                        "full_target": target
                    })
                    all_symbols.add(source_name)
                    all_symbols.add(target_name)
            
            # Создаем узлы с метаданными
            nodes = []
            for symbol in all_symbols:
                # Определяем тип модуля по пути
                module_type = "unknown"
                color = "#9CA3AF"
                
                if "api" in symbol:
                    module_type = "api"
                    color = "#3B82F6"  # blue
                elif "llm" in symbol:
                    module_type = "llm"
                    color = "#EF4444"  # red  
                elif "db" in symbol or "models" in symbol:
                    module_type = "database"
                    color = "#10B981"  # green
                elif "admin" in symbol:
                    module_type = "admin"
                    color = "#8B5CF6"  # purple
                elif "graph" in symbol:
                    module_type = "graph"
                    color = "#F59E0B"  # amber
                elif "utils" in symbol:
                    module_type = "utils"
                    color = "#6B7280"  # gray
                
                # Подсчитываем связи для размера узла
                incoming = sum(1 for link in links if link["target"] == symbol)
                outgoing = sum(1 for link in links if link["source"] == symbol)
                total_connections = incoming + outgoing
                
                nodes.append({
                    "id": symbol,
                    "name": symbol,
                    "type": module_type,
                    "color": color,
                    "size": min(10 + total_connections * 2, 50),  # Размер от 10 до 50
                    "incoming": incoming,
                    "outgoing": outgoing,
                    "total_connections": total_connections
                })
            
            # Статистика
            stats = {
                "total_nodes": len(nodes),
                "total_edges": len(links),
                "module_types": {}
            }
            
            for node in nodes:
                module_type = node["type"]
                if module_type not in stats["module_types"]:
                    stats["module_types"][module_type] = 0
                stats["module_types"][module_type] += 1
        
        log.info(
            event="api_call_end",
            env=get_env(),
            component="ui",
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_call_graph",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/call-graph",
                "status": 200,
                "nodes_count": len(nodes),
                "links_count": len(links)
            }
        )
        
        return {
            "nodes": nodes,
            "links": links,
            "stats": stats,
            "metadata": {
                "generated_at": correlation_id,
                "max_nodes_requested": max_nodes,
                "module_filter": module_filter
            }
        }
        
    except Exception as e:
        log.error(
            event="api_call_end",
            env=get_env(),
            component="ui", 
            agent_role="Dev",
            run_id=correlation_id,
            task_id="admin_call_graph",
            correlation_id=correlation_id,
            kv={
                "method": "GET",
                "url_host": request.url.hostname or "localhost",
                "url_path": "/admin/call-graph",
                "status": 500,
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise HTTPException(status_code=500, detail=str(e))
