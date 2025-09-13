from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
import subprocess
from typing import Dict, Any, List
from app.db.session import get_db
from app.logging_helpers import log, get_env, generate_correlation_id
from app.llm.cli_path_guard import get_health_check_result
from app.api.middleware import get_correlation_id

# Import llm_status directly for light check
from app.api.llm_status import llm_status as get_llm_status_light # Renamed to avoid conflict

router = APIRouter(prefix="/health")

def check_database_health(db: Session) -> Dict[str, Any]:
    """Проверяет состояние подключения к базе данных."""
    try:
        # Выполняем простой запрос к БД для проверки подключения
        db.execute(text("SELECT 1"))
        return {"status": "ok", "component": "database"}
    except Exception as e:
        log.error(
            event="healthcheck",
            env=get_env(),
            component="health",
            agent_role="System",
            correlation_id="health-check",
            kv={"component": "database", "status": "error", "error": str(e)}
        )
        return {"status": "error", "component": "database", "error": str(e)}

def check_migrations_health(db: Session) -> Dict[str, Any]:
    """Проверяет, применены ли все миграции."""
    try:
        # Проверяем текущую версию миграций
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        return {"status": "ok", "component": "migrations", "version": version}
    except Exception as e:
        log.error(
            event="healthcheck",
            env=get_env(),
            component="health",
            agent_role="System",
            correlation_id="health-check",
            kv={"component": "migrations", "status": "error", "error": str(e)}
        )
        return {"status": "error", "component": "migrations", "error": str(e)}

def check_index_files_health() -> Dict[str, Any]:
    """Проверяет наличие индексных файлов."""
    try:
        # Проверяем наличие файлов индекса
        base_path = "/opt/feature-factory/data"
        required_files = ["code_registry.jsonl", "symbol_index.jsonl", "call_graph.dot"]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(os.path.join(base_path, file)):
                missing_files.append(file)
        
        if missing_files:
            return {"status": "error", "component": "index_files", "missing": missing_files}
        else:
            return {"status": "ok", "component": "index_files"}
    except Exception as e:
        log.error(
            event="healthcheck",
            env=get_env(),
            component="health",
            agent_role="System",
            correlation_id="health-check",
            kv={"component": "index_files", "status": "error", "error": str(e)}
        )
        return {"status": "error", "component": "index_files", "error": str(e)}

def check_llm_cli_health() -> Dict[str, Any]:
    """Проверяет работоспособность LLM CLI провайдеров."""
    try:
        # Используем новый модуль для проверки CLI зависимостей
        return get_health_check_result()
    except Exception as e:
        log.error(
            event="healthcheck",
            env=get_env(),
            component="health",
            agent_role="System",
            correlation_id="health-check",
            kv={"component": "llm_cli", "status": "error", "error": str(e)}
        )
        return {"status": "error", "component": "llm_cli", "error": str(e)}

# Removed check_llm_status_health function

def check_llm_api_light() -> Dict[str, Any]:
    """Легкая проверка статуса LLM API без HTTP-запросов."""
    try:
        # Используем импортированную функцию llm_status напрямую
        # Это не HTTP-вызов, а прямое использование логики
        status_data = get_llm_status_light()
        return {"status": "ok", "component": "llm_api", "details": status_data}
    except Exception as e:
        log.error(
            event="healthcheck",
            env=get_env(),
            component="health",
            agent_role="System",
            correlation_id="health-check",
            kv={"component": "llm_api", "status": "error", "error": str(e)}
        )
        return {"status": "error", "component": "llm_api", "error": str(e)}


@router.get("/live")
async def health_live(request: Request):
    """
    Эндпоинт для проверки живости приложения.
    Всегда возвращает 200, если приложение запущено.
    """
    correlation_id = get_correlation_id(request)
    
    log.info(
        event="healthcheck",
        env=get_env(),
        component="health",
        agent_role="System",
        correlation_id=correlation_id,
        kv={"component": "live", "status": "ok"}
    )
    return {"status": "ok", "component": "live"}

@router.get("/ready", status_code=status.HTTP_200_OK) # Default to 200 OK
async def health_ready(request: Request, db: Session = Depends(get_db)):
    """
    Эндпоинт для проверки готовности приложения к работе.
    Проверяет подключение к БД, применение миграций, наличие индексных файлов и статус LLM API.
    """
    correlation_id = get_correlation_id(request)
    checks: List[Dict[str, Any]] = []
    
    # Wrap each check in a try-except to prevent exceptions from propagating
    try:
        checks.append(check_database_health(db))
    except Exception as e:
        checks.append({"status": "error", "component": "database", "error": str(e)})

    try:
        checks.append(check_migrations_health(db))
    except Exception as e:
        checks.append({"status": "error", "component": "migrations", "error": str(e)})

    try:
        checks.append(check_index_files_health())
    except Exception as e:
        checks.append({"status": "error", "component": "index_files", "error": str(e)})

    try:
        checks.append(check_llm_api_light()) # Using light LLM API check
    except Exception as e:
        checks.append({"status": "error", "component": "llm_api", "error": str(e)})
    
    # Проверяем, все ли проверки успешны
    all_healthy = all(check["status"] == "ok" for check in checks)
    
    # Логируем результат
    log.info(
        event="healthcheck",
        env=get_env(),
        component="health",
        agent_role="System",
        correlation_id=correlation_id,
        kv={"component": "ready", "status": "ok" if all_healthy else "error", "checks": checks}
    )
    
    if all_healthy:
        return {"status": "ok", "component": "ready", "checks": checks}
    else:
        # Return 503 if not all checks are healthy
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "component": "ready", "checks": checks}
        )

@router.get("/")
async def health():
    """
    Простой эндпоинт для проверки состояния приложения.
    Возвращает {"status": "ok"}.
    """
    return {"status": "ok"}

@router.get("/deps")
async def health_deps():
    """
    Эндпоинт для проверки зависимостей приложения.
    Проверяет работоспособность CLI бинарников для каждого провайдера LLM.
    """
    llm_check = check_llm_cli_health()
    
    # Логируем результат
    log.info(
        event="healthcheck",
        env=get_env(),
        component="health",
        agent_role="System",
        correlation_id="health-check",
        kv={"component": "deps", "status": llm_check["status"], "checks": [llm_check]}
    )
    
    if llm_check["status"] == "ok":
        return {"status": "ok", "component": "deps", "checks": [llm_check]}
    else:
        return {"status": "error", "component": "deps", "checks": [llm_check]}