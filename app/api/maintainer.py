#!/usr/bin/env python3
"""
API для maintainer, реализация по спецификации API-Maintainer-001.md.
"""

import time
import uuid
import os
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Импортируем схемы
from app.api.schemas.maintainer_schemas import (
    MaintainerIntentRequest,
    MaintainerPlanRequest,
    MaintainerIntentResponse,
    MaintainerPlanResponse,
    TaskDSL,
    ErrorResponse
)

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Создаем роутер
router = APIRouter(prefix="/api/v1/maintainer")


# Вспомогательные функции
def get_correlation_id(request: Request) -> str:
    """Получает correlation_id из заголовков запроса."""
    return request.headers.get("x-correlation-id", generate_correlation_id())


def log_api_call_start(request: Request, correlation_id: str, **kwargs):
    """Логирует начало API вызова."""
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="Maintainer",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            **kwargs
        }
    )


def log_api_call_end(request: Request, correlation_id: str, status_code: int, duration_ms: float, **kwargs):
    """Логирует завершение API вызова."""
    log.info(
        event="api_call_end",
        env=get_env(),
        component="api",
        agent_role="Maintainer",
        run_id=correlation_id,
        task_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            **kwargs
        }
    )


# Эндпоинты API
@router.post("/intent",
             response_model=MaintainerIntentResponse,
             responses={
                 400: {"model": ErrorResponse},
                 429: {"model": ErrorResponse},
                 500: {"model": ErrorResponse}
             })
async def generate_intent(
    request: Request,
    intent_request: MaintainerIntentRequest
):
    """
    Генерирует intent из текста на естественном языке.
    
    Args:
        request: HTTP запрос
        intent_request: Данные для генерации intent
        
    Returns:
        MaintainerIntentResponse: Сгенерированный intent
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        nl_text=intent_request.nl_text
    )
    
    try:
        # Проверяем, что текст не пустой
        if not intent_request.nl_text.strip():
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=400,
                duration_ms=duration_ms,
                error="EMPTY_NL_TEXT"
            )
            
            raise HTTPException(
                status_code=400,
                detail="Natural language text is required",
                headers={"error": "EMPTY_NL_TEXT"}
            )
        
        # В реальной реализации здесь будет вызов LLM для генерации intent
        # Для демонстрации создаем простой intent
        
        # Создаем intent_json
        intent_json = {
            "intent": "create_feature",
            "title": intent_request.nl_text[:50],  # Первые 50 символов как заголовок
            "description": intent_request.nl_text,
            "priority": 1
        }
        
        # Создаем issues и suggestions
        issues = []
        suggestions = [
            "Рассмотрите возможность добавления тестов для этой фичи",
            "Обновите документацию после реализации"
        ]
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return MaintainerIntentResponse(
            nl_text=intent_request.nl_text,
            intent_json=intent_json,
            issues=issues,
            suggestions=suggestions
        )
        
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Maintainer",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
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
            detail=f"Failed to generate intent: {str(e)}",
            headers={"error": "INTERNAL_ERROR"}
        )


@router.post("/plan",
             response_model=MaintainerPlanResponse,
             responses={
                 400: {"model": ErrorResponse},
                 429: {"model": ErrorResponse},
                 500: {"model": ErrorResponse}
             })
async def generate_plan(
    request: Request,
    plan_request: MaintainerPlanRequest
):
    """
    Генерирует план выполнения из intent.
    
    Args:
        request: HTTP запрос
        plan_request: Данные для генерации плана
        
    Returns:
        MaintainerPlanResponse: Сгенерированный план
    """
    start_time = time.time()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(
        request,
        correlation_id,
        intent_json=plan_request.intent_json
    )
    
    try:
        # Проверяем, что intent_json не пустой
        if not plan_request.intent_json:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call_end(
                request,
                correlation_id,
                status_code=400,
                duration_ms=duration_ms,
                error="EMPTY_INTENT_JSON"
            )
            
            raise HTTPException(
                status_code=400,
                detail="Intent JSON is required",
                headers={"error": "EMPTY_INTENT_JSON"}
            )
        
        # В реальной реализации здесь будет вызов Architect для генерации плана
        # Для демонстрации создаем простой план
        
        # Создаем DAG задач
        dag = [
            TaskDSL(
                id=str(uuid.uuid4()),
                name="design_schema",
                kind="code",
                role="Architect",
                preconditions=[],
                postconditions=["schema_designed"],
                idempotency_key="architect.schema.v1",
                retry={"max": 1, "backoff": "exp:10,30"},
                deadline="PT15M",
                models=["claude", "gpt", "gemini-fallback"],
                outputs=["files"],
                dod=[
                    "Схема базы данных определена",
                    "Миграции созданы"
                ],
                severity="high"
            ),
            TaskDSL(
                id=str(uuid.uuid4()),
                name="implement_feature",
                kind="code",
                role="Dev",
                preconditions=["schema_designed"],
                postconditions=["feature_implemented"],
                idempotency_key="dev.feature.v1",
                retry={"max": 2, "backoff": "exp:5,30,120"},
                deadline="PT30M",
                models=["qwen", "gemini"],
                outputs=["files", "logs"],
                dod=[
                    "Код реализован согласно схеме",
                    "Юнит-тесты написаны"
                ],
                severity="high"
            ),
            TaskDSL(
                id=str(uuid.uuid4()),
                name="run_tests",
                kind="test",
                role="QA",
                preconditions=["feature_implemented"],
                postconditions=["tests_passed"],
                idempotency_key="qa.tests.v1",
                retry={"max": 1, "backoff": "exp:10,60"},
                deadline="PT20M",
                models=["gemini", "qwen"],
                outputs=["tests", "report"],
                dod=[
                    "Интеграционные тесты пройдены",
                    "E2E тесты выполнены"
                ],
                severity="med"
            ),
            TaskDSL(
                id=str(uuid.uuid4()),
                name="update_documentation",
                kind="doc",
                role="Scribe",
                preconditions=["tests_passed"],
                postconditions=["docs_updated"],
                idempotency_key="scribe.docs.v1",
                retry={"max": 1, "backoff": "exp:10,60"},
                deadline="PT15M",
                models=["gemini", "qwen"],
                outputs=["files"],
                dod=[
                    "Документация обновлена",
                    "CHANGELOG дополнен"
                ],
                severity="low"
            )
        ]
        
        # Создаем package_contract
        package_contract = {
            "feature_id": 1,
            "version": "1.0",
            "description": "Auto-generated package contract"
        }
        
        # Логируем успешное завершение вызова
        duration_ms = (time.time() - start_time) * 1000
        log_api_call_end(
            request,
            correlation_id,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return MaintainerPlanResponse(
            intent_json=plan_request.intent_json,
            dag=dag,
            package_contract=package_contract
        )
        
    except HTTPException:
        # Перебрасываем HTTP исключения без изменений
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="Maintainer",
            run_id=correlation_id,
            task_id=str(uuid.uuid4()),
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
            detail=f"Failed to generate plan: {str(e)}",
            headers={"error": "INTERNAL_ERROR"}
        )