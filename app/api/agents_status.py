#!/usr/bin/env python3
"""
API эндпоинты для кэшированного статуса агентов с поддержкой SWR.
"""

from __future__ import annotations
from fastapi import APIRouter, Query
from typing import Dict, Any
from app.services.agents_status import agents_status_service

router = APIRouter(prefix="/api/v1/agents")


@router.get("/status")
def get_agents_status(fresh: bool = Query(False, description="Принудительно обновить кэш")) -> Dict[str, Any]:
    """
    Получить статус агентов. 
    Если fresh=False (по умолчанию), возвращает кэшированные данные (≤100мс).
    Если fresh=True, принудительно обновляет кэш.
    
    Response format:
    {
        "as_of": "2025-08-30T09:15:00.123456",
        "stale": false,
        "items": [
            {
                "model": "claude",
                "provider": "claude", 
                "status": "ok",
                "oauth_ok": true,
                "tokens_used": 45000,
                "latency_ms": 234,
                "checked_at": "2025-08-30T09:15:00.123456",
                "expires_at": "2025-08-30T09:20:00.123456",
                "binary_path": "/opt/feature-factory/bin/claude",
                "probe_command": "claude --version",
                "local_config_exists": true,
                "has_refresh_token": true
            }
        ]
    }
    """
    return agents_status_service.get_cached_status(fresh=fresh)


@router.post("/refresh")
def refresh_agents_status() -> Dict[str, Any]:
    """
    Запустить фоновое обновление кэша агентов.
    Возвращает job_id для отслеживания операции.
    
    Response format:
    {
        "job_id": "refresh_1693234567",
        "accepted": true
    }
    """
    return agents_status_service.refresh_async()