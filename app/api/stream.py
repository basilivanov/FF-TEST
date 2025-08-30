#!/usr/bin/env python3
"""
Эндпоинт для Server-Sent Events (SSE), реализация по спецификации UI-000.md.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, text

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Создаем роутер
router = APIRouter(prefix="/api/v1")


async def event_generator(request: Request):
    """
    Генератор событий для SSE.
    
    Args:
        request: HTTP запрос
        
    Yields:
        Строки с событиями в формате SSE
    """
    # Генерируем уникальный ID для этого соединения
    connection_id = str(uuid.uuid4())
    
    # Логируем начало соединения
    log.info(
        event="sse_connection_start",
        env=get_env(),
        component="sse",
        agent_role="System",
        run_id=connection_id,
        task_id=connection_id,
        correlation_id=connection_id,
        kv={
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    try:
        # Отправляем событие подключения
        yield f"event: connection_opened\\ndata: {json.dumps({'connection_id': connection_id})}\\n\\n"
        
        # Счетчик для генерации тестовых событий
        counter = 0
        
        # Бесконечный цикл для отправки событий
        while True:
            # Проверяем, не закрыто ли соединение
            if await request.is_disconnected():
                break
                
            # Генерируем тестовые события (в реальной реализации события будут приходить из системы)
            counter += 1
            
            # Генерируем различные типы событий
            if counter % 10 == 1:
                # Событие начала задачи
                event_data = {
                    "job_id": f"job-{counter}",
                    "task_id": f"task-{counter}",
                    "run_id": f"run-{counter}",
                    "correlation_id": generate_correlation_id(),
                    "timestamp": time.time()
                }
                yield f"event: job_started\\ndata: {json.dumps(event_data)}\\n\\n"
                
            elif counter % 10 == 3:
                # Событие завершения задачи
                event_data = {
                    "job_id": f"job-{counter-2}",
                    "task_id": f"task-{counter-2}",
                    "run_id": f"run-{counter-2}",
                    "correlation_id": generate_correlation_id(),
                    "timestamp": time.time(),
                    "result": "success"
                }
                yield f"event: job_finished\\ndata: {json.dumps(event_data)}\\n\\n"
                
            elif counter % 10 == 5:
                # Событие ошибки
                event_data = {
                    "job_id": f"job-{counter-4}",
                    "task_id": f"task-{counter-4}",
                    "run_id": f"run-{counter-4}",
                    "correlation_id": generate_correlation_id(),
                    "timestamp": time.time(),
                    "error": "Test error",
                    "error_type": "TestError"
                }
                yield f"event: error\\ndata: {json.dumps(event_data)}\\n\\n"
                
            elif counter % 10 == 7:
                # Событие обновления индекса
                event_data = {
                    "index_id": f"index-{counter}",
                    "run_id": f"run-{counter}",
                    "correlation_id": generate_correlation_id(),
                    "timestamp": time.time(),
                    "files_processed": counter * 10
                }
                yield f"event: index_updated\\ndata: {json.dumps(event_data)}\\n\\n"
                
            elif counter % 10 == 9:
                # Событие обновления документации
                event_data = {
                    "doc_id": f"doc-{counter}",
                    "run_id": f"run-{counter}",
                    "correlation_id": generate_correlation_id(),
                    "timestamp": time.time(),
                    "doc_name": f"Document {counter}"
                }
                yield f"event: doc_updated\\ndata: {json.dumps(event_data)}\\n\\n"
                
            # Ждем 1 секунду перед следующей итерацией
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        # Логируем закрытие соединения
        log.info(
            event="sse_connection_closed",
            env=get_env(),
            component="sse",
            agent_role="System",
            run_id=connection_id,
            task_id=connection_id,
            correlation_id=connection_id,
            kv={
                "reason": "cancelled"
            }
        )
        raise
    except Exception as e:
        # Логируем ошибку
        log.error(
            event="sse_connection_error",
            env=get_env(),
            component="sse",
            agent_role="System",
            run_id=connection_id,
            task_id=connection_id,
            correlation_id=connection_id,
            kv={
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise
    finally:
        # Отправляем событие закрытия соединения
        yield f"event: connection_closed\\ndata: {json.dumps({'connection_id': connection_id})}\\n\\n"


@router.get("/stream/events")
async def stream_events(request: Request):
    """
    Эндпоинт для Server-Sent Events.
    
    Args:
        request: HTTP запрос
        
    Returns:
        StreamingResponse: Поток событий в формате SSE
    """
    # Логируем начало стриминга
    correlation_id = generate_correlation_id()
    log.info(
        event="sse_stream_start",
        env=get_env(),
        component="sse",
        agent_role="System",
        run_id=correlation_id,
        task_id=correlation_id,
        correlation_id=correlation_id
    )
    
    # Возвращаем StreamingResponse с генератором событий
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )