#!/usr/bin/env python3
"""
API для операций (ops).
"""

import yaml
import json
import os
from fastapi import APIRouter, HTTPException, Request
from app.logging_helpers import log, get_env, generate_correlation_id

# Создаем роутер
router = APIRouter(prefix="/ops")

SUDO_WRAPPERS_CONFIG_PATH = "/opt/feature-factory/configs/ops/sudo_wrappers.yaml"

@router.get("/wrappers",
             responses={
                 500: {"model": dict} # Using dict as a placeholder for ErrorResponse
             })
async def get_sudo_wrappers(request: Request):
    """
    Получить список доступных sudo-оберток.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[Dict]: Список sudo-оберток
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()
    
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Ops",
        run_id=correlation_id,
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "endpoint": "GET /ops/wrappers"
        }
    )
    
    try:
        if not os.path.exists(SUDO_WRAPPERS_CONFIG_PATH):
            log.error(
                event="sudo_wrappers_config_not_found",
                env=get_env(),
                component="api",
                agent_role="Ops",
                run_id=correlation_id,
                correlation_id=correlation_id,
                kv={"path": SUDO_WRAPPERS_CONFIG_PATH}
            )
            raise HTTPException(
                status_code=500,
                detail="Sudo wrappers configuration file not found",
                headers={"error_code": "CONFIG_NOT_FOUND"}
            )
            
        with open(SUDO_WRAPPERS_CONFIG_PATH, 'r') as f:
            config_content = yaml.safe_load(f)
            
        wrappers = config_content.get("wrappers", [])
        
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Ops",
            run_id=correlation_id,
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_host": request.url.hostname or "localhost",
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(duration_ms, 2),
                "wrappers_count": len(wrappers)
            }
        )
        
        return wrappers
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Ops",
            run_id=correlation_id,
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
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get sudo wrappers: {str(e)}",
            headers={"error_code": "INTERNAL_ERROR"}
        )
