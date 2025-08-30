#!/usr/bin/env python3
"""
Middleware для FastAPI, обеспечивающий сквозную корреляцию запросов.
"""

import uuid
from typing import Callable, Awaitable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import os
import structlog

# Настройка structlog для JSON логов
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# Глобальный логгер
log = structlog.get_logger()


def get_env() -> str:
    """Получает текущее окружение (test или prod)."""
    return os.getenv("ENV", "test")


class CorrelationIdMiddleware:
    """
    Middleware для генерации и прокидывания correlation_id.
    """
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        
        if scope["type"] == "websocket":
            # Для WebSocket просто пропускаем без обработки correlation_id
            await self.app(scope, receive, send)
            return

        # Извлекаем заголовки напрямую из scope
        headers = dict(scope.get("headers", []))
        correlation_id_bytes = headers.get(b"x-correlation-id")
        
        # Проверяем наличие correlation_id в заголовках
        correlation_id = correlation_id_bytes.decode() if correlation_id_bytes else None
        if not correlation_id:
            # Генерируем новый correlation_id если его нет
            correlation_id = str(uuid.uuid4())
        
        # Добавляем correlation_id в scope
        scope["correlation_id"] = correlation_id
        scope["env"] = get_env()
        
        # Создаем обертку для send, чтобы добавить заголовки в ответ
        async def send_with_correlation_id(message):
            if message["type"] == "http.response.start":
                # Добавляем correlation_id в заголовки ответа
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode()))
                message["headers"] = headers
            await send(message)
        
        try:
            await self.app(scope, receive, send_with_correlation_id)
        except Exception as e:
            # Вместо re-raise, формируем JSONResponse с correlation_id
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error", "correlation_id": correlation_id},
                headers={"x-correlation-id": correlation_id}
            )
            await response(scope, receive, send)
            return # Важно: не re-raise, а завершаем обработку


def get_correlation_id(request: Request) -> str:
    """
    Получает correlation_id из request scope.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        str: correlation_id
    """
    # Получаем correlation_id из scope
    return request.scope.get("correlation_id", str(uuid.uuid4()))


def get_env_from_scope(request: Request) -> str:
    """
    Получает окружение из request scope.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        str: окружение (test или prod)
    """
    # Получаем окружение из scope
    return request.scope.get("env", "test")