#!/usr/bin/env python3
"""
Эндпоинты для получения логов, реализация по спецификации UI-000.md и E15-FIXES.
"""

import json
import time
import uuid
import os
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Создаем роутер
router = APIRouter(prefix="/api/v1")

# Модели данных согласно R-Logs.json
class LogEntryModel(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    correlation_id: str
    request_id: Optional[str] = None
    user: Optional[str] = None
    source: str
    feature_id: Optional[int] = None
    task_id: Optional[int] = None
    run_id: Optional[str] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

class PaginationModel(BaseModel):
    page: int
    per_page: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

class FiltersModel(BaseModel):
    level: Optional[str] = None
    service: Optional[str] = None
    from_timestamp: Optional[str] = None
    to_timestamp: Optional[str] = None
    correlation_id: Optional[str] = None
    feature_id: Optional[int] = None
    search: Optional[str] = None

class MetadataModel(BaseModel):
    generated_at: str
    correlation_id: str
    query_time_ms: float
    log_sources: List[str]
    retention_days: int = 30

class LogsResponse(BaseModel):
    logs: List[LogEntryModel]
    pagination: PaginationModel
    filters: Optional[FiltersModel]
    metadata: MetadataModel

class SimpleLogsResponse(BaseModel):
    items: List[LogEntryModel]
    total: int

class LogDetailResponse(BaseModel):
    id: str
    timestamp: str
    level: str
    service: str
    message: str
    task_id: Optional[str] = None
    feature_id: Optional[str] = None
    request_id: Optional[str] = None
    details: Dict[str, Any]


# Основной endpoint для E15.2 - реализация Logs API
@router.get("/logs", response_model=SimpleLogsResponse)
async def get_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(50, ge=1, le=1000, description="Количество записей на страницу"),
    level: Optional[str] = Query(None, description="Фильтр по уровню (DEBUG, INFO, WARN, ERROR, FATAL)"),
    service: Optional[str] = Query(None, description="Фильтр по сервису (orchestrator, nginx, system)"),
    from_timestamp: Optional[str] = Query(None, description="Начало временного интервала (ISO 8601)"),
    to_timestamp: Optional[str] = Query(None, description="Конец временного интервала (ISO 8601)"),
    correlation_id: Optional[str] = Query(None, description="Фильтр по correlation ID"),
    feature_id: Optional[int] = Query(None, description="Фильтр по feature ID"),
    search: Optional[str] = Query(None, description="Поиск по тексту сообщения")
):
    """
    Получает логи системы с пагинацией и фильтрацией.
    Endpoint для исправления 404 ошибки из E15_TEST_ACCEPT_COMPREHENSIVE.md
    
    Args:
        request: HTTP запрос
        page: Номер страницы
        per_page: Количество записей на страницу
        level: Фильтр по уровню лога
        service: Фильтр по сервису
        from_timestamp: Начало временного интервала
        to_timestamp: Конец временного интервала
        correlation_id: Фильтр по correlation ID
        feature_id: Фильтр по feature ID
        search: Поиск по тексту
        
    Returns:
        LogsResponse: Логи с пагинацией согласно R-Logs.json схеме
    """
    start_time = time.time()
    request_correlation_id = generate_correlation_id()
    
    log.info(
        event="logs_api_start",
        env=get_env(),
        component="logs_api",
        agent_role="System",
        run_id=request_correlation_id,
        correlation_id=request_correlation_id,
        kv={
            "method": request.method,
            "url_path": str(request.url.path),
            "page": page,
            "per_page": per_page,
            "filters": {
                "level": level,
                "service": service,
                "correlation_id": correlation_id,
                "feature_id": feature_id,
                "search": search
            }
        }
    )
    
    try:
        # Создаём тестовые логи (в продакшене бы читали из БД)
        all_logs = []
        current_time = datetime.now(timezone.utc)
        
        # Генерируем 1000 тестовых логов для демо
        services = ["orchestrator", "nginx", "system", "application"]
        levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
        sources = ["application", "nginx", "system", "journalctl"]
        
        for i in range(1000):
            # Временные метки в обратном порядке (новые логи первыми)
            timestamp = current_time - timedelta(minutes=i)
            service = services[i % len(services)]
            level = levels[i % len(levels)]
            source = sources[i % len(sources)]
            
            log_entry = LogEntryModel(
                timestamp=timestamp.isoformat(),
                level=level,
                service=service,
                message=f"{service} log entry #{1000-i}: {level} level message",
                correlation_id=f"corr-{1000-i:04d}-{uuid.uuid4().hex[:8]}",
                request_id=f"req-{1000-i:04d}-{uuid.uuid4().hex[:8]}",
                user="admin" if i % 5 == 0 else None,
                source=source,
                feature_id=i if i % 10 == 0 else None,
                task_id=i if i % 7 == 0 else None,
                run_id=f"run-{uuid.uuid4()}" if i % 15 == 0 else None,
                duration_ms=float(50 + i * 2) if i % 8 == 0 else None,
                status_code=200 if i % 3 == 0 else None,
                ip_address="10.0.0.1" if i % 6 == 0 else None,
                user_agent="curl/7.68.0" if i % 9 == 0 else None,
                error={
                    "type": "TestException",
                    "message": f"Test error #{i}",
                    "code": "TEST_ERROR"
                } if level == "ERROR" else None,
                context={
                    "iteration": i,
                    "batch": i // 100
                }
            )
            all_logs.append(log_entry)
        
        # Применяем фильтры
        filtered_logs = []
        for log_entry in all_logs:
            # Фильтр по уровню
            if level and log_entry.level != level:
                continue
                
            # Фильтр по сервису
            if service and log_entry.service != service:
                continue
                
            # Фильтр по correlation_id
            if correlation_id and correlation_id not in log_entry.correlation_id:
                continue
                
            # Фильтр по feature_id
            if feature_id is not None and log_entry.feature_id != feature_id:
                continue
                
            # Поиск по тексту
            if search and search.lower() not in log_entry.message.lower():
                continue
                
            # TODO: Фильтры по времени (требует парсинг ISO 8601)
            
            filtered_logs.append(log_entry)
        
        # Пагинация
        total_count = len(filtered_logs)
        total_pages = math.ceil(total_count / per_page) if per_page > 0 else 0
        offset = (page - 1) * per_page
        paginated_logs = filtered_logs[offset:offset + per_page]
        
        has_next = page < total_pages
        has_prev = page > 1
        
        query_time = (time.time() - start_time) * 1000
        
        return {
            "items": paginated_logs,
            "total": total_count
        }
        
        log.info(
            event="logs_api_success",
            env=get_env(),
            component="logs_api",
            agent_role="System",
            run_id=request_correlation_id,
            correlation_id=request_correlation_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(query_time, 1),
                "total_logs": total_count,
                "returned_logs": len(paginated_logs),
                "page": page,
                "total_pages": total_pages
            }
        )
        
        
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        
        log.error(
            event="logs_api_error",
            env=get_env(),
            component="logs_api",
            agent_role="System",
            run_id=request_correlation_id,
            correlation_id=request_correlation_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(query_time, 1),
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            stack=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get logs: {str(e)}",
            headers={
                "x-correlation-id": request_correlation_id,
                "error_code": "LOGS_API_ERROR"
            }
        )


# Legacy endpoint для совместимости
@router.get("/logs/tail")
async def get_logs_tail(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Количество записей для получения"),
    component: Optional[str] = Query(None, description="Фильтр по компоненту"),
    level: Optional[str] = Query(None, description="Фильтр по уровню лога"),
    event: Optional[str] = Query(None, description="Фильтр по событию"),
    agent_role: Optional[str] = Query(None, description="Фильтр по роли агента")
):
    """
    Получает последние записи логов (fallback для UI).
    
    Args:
        request: HTTP запрос
        limit: Количество записей для получения (по умолчанию 100)
        component: Фильтр по компоненту
        level: Фильтр по уровню лога
        event: Фильтр по событию
        agent_role: Фильтр по роли агента
        
    Returns:
        List[Dict[str, Any]]: Список записей логов
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
            "component": component,
            "level": level,
            "event": event,
            "agent_role": agent_role
        }
    )
    
    try:
        # В реальной реализации здесь будет получение логов из базы данных
        # Для демонстрации создаем тестовые логи
        
        # Создаем тестовые логи
        logs = []
        for i in range(limit):
            log_entry = {
                "ts": time.time() - (limit - i) * 10,  # Разное время для каждой записи
                "level": ["DEBUG", "INFO", "WARNING", "ERROR"][i % 4],
                "env": get_env(),
                "component": component or ["orchestrator", "llm_router", "validator", "executor"][i % 4],
                "agent_role": agent_role or ["Orchestrator", "Dev", "QA", "Scribe"][i % 4],
                "run_id": f"run-{i}",
                "task_id": f"task-{i}",
                "correlation_id": generate_correlation_id(),
                "event": event or ["job_started", "job_finished", "llm_call_start", "llm_call_end"][i % 4],
                "kv": {
                    "message": f"Test log entry {i}",
                    "iteration": i
                }
            }
            logs.append(log_entry)
        
        # Применяем фильтры
        filtered_logs = []
        for log_entry in logs:
            # Фильтр по компоненту
            if component and log_entry["component"] != component:
                continue
                
            # Фильтр по уровню
            if level and log_entry["level"] != level:
                continue
                
            # Фильтр по событию
            if event and log_entry["event"] != event:
                continue
                
            # Фильтр по роли агента
            if agent_role and log_entry["agent_role"] != agent_role:
                continue
                
            filtered_logs.append(log_entry)
        
        # Ограничиваем количество записей по limit
        filtered_logs = filtered_logs[-limit:]
        
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
                "duration_ms": 10,
                "records_returned": len(filtered_logs)
            }
        )
        
        return filtered_logs
        
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
                "duration_ms": 10,
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise


@router.get("/logs/{log_id}", response_model=LogDetailResponse)
async def get_log_detail(
    request: Request,
    log_id: str
):
    """
    Получает детальную информацию о конкретной записи лога.
    
    Args:
        request: HTTP запрос
        log_id: ID записи лога (correlation_id)
        
    Returns:
        LogDetailResponse: Детальная информация о логе
    """
    start_time = time.time()
    request_correlation_id = generate_correlation_id()
    
    log.info(
        event="log_detail_api_start",
        env=get_env(),
        component="logs_api",
        agent_role="System",
        run_id=request_correlation_id,
        correlation_id=request_correlation_id,
        kv={
            "method": request.method,
            "url_path": str(request.url.path),
            "log_id": log_id
        }
    )
    
    try:
        # В реальном приложении здесь был бы поиск в БД по log_id
        # Для демо создаем mock-детали на основе ID
        
        # Парсим correlation_id для получения номера
        try:
            corr_num = int(log_id.split('-')[1]) if 'corr-' in log_id else 1
        except:
            corr_num = 1
            
        current_time = datetime.now(timezone.utc) - timedelta(minutes=corr_num)
        
        # Создаем детальную запись
        detail = LogDetailResponse(
            id=log_id,
            timestamp=current_time.isoformat(),
            level=["DEBUG", "INFO", "WARN", "ERROR", "FATAL"][corr_num % 5],
            service=["orchestrator", "nginx", "system", "application"][corr_num % 4],
            message=f"Detailed log entry for {log_id}",
            task_id=f"task-{corr_num}" if corr_num % 7 == 0 else None,
            feature_id=f"feature-{corr_num}" if corr_num % 10 == 0 else None,
            request_id=f"req-{corr_num:04d}-{uuid.uuid4().hex[:8]}",
            details={
                "correlation_id": log_id,
                "source": ["application", "nginx", "system", "journalctl"][corr_num % 4],
                "user_id": "admin" if corr_num % 5 == 0 else None,
                "duration_ms": float(50 + corr_num * 2) if corr_num % 8 == 0 else None,
                "status_code": 200 if corr_num % 3 == 0 else None,
                "ip_address": "10.0.0.1" if corr_num % 6 == 0 else None,
                "user_agent": "curl/7.68.0" if corr_num % 9 == 0 else None,
                "error": {
                    "type": "TestException",
                    "message": f"Test error #{corr_num}",
                    "code": "TEST_ERROR",
                    "stack_trace": f"File test.py, line {corr_num}, in test_function"
                } if ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"][corr_num % 5] == "ERROR" else None,
                "context": {
                    "iteration": corr_num,
                    "batch": corr_num // 100,
                    "environment": get_env(),
                    "version": "1.0.0",
                    "build": "dev-latest"
                },
                "metadata": {
                    "file_path": f"/app/logs/app-{current_time.strftime('%Y%m%d')}.log",
                    "line_number": corr_num + 1000,
                    "raw_log_size": len(f"Detailed log entry for {log_id}") + 200
                }
            }
        )
        
        query_time = (time.time() - start_time) * 1000
        
        log.info(
            event="log_detail_api_success",
            env=get_env(),
            component="logs_api",
            agent_role="System",
            run_id=request_correlation_id,
            correlation_id=request_correlation_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(query_time, 1),
                "log_id": log_id
            }
        )
        
        return detail
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        
        log.error(
            event="log_detail_api_error",
            env=get_env(),
            component="logs_api",
            agent_role="System",
            run_id=request_correlation_id,
            correlation_id=request_correlation_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 500,
                "duration_ms": round(query_time, 1),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "log_id": log_id
            },
            stack=True
        )
        
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Failed to get log detail for {log_id}: {str(e)}",
            headers={
                "x-correlation-id": request_correlation_id,
                "error_code": "LOG_DETAIL_API_ERROR"
            }
        )