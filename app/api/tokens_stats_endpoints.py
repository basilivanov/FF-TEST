#!/usr/bin/env python3
"""
Эндпоинты для получения статистики токенов.
"""

import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Создаем роутер
router = APIRouter(prefix="/api/v1/admin")
security = HTTPBasic()

# Конфигурация аутентификации
AUTH_USERNAME = os.getenv("ADMIN_USERNAME", "ops")
AUTH_PASSWORD = os.getenv("ADMIN_PASSWORD", "ops123")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка BasicAuth для admin endpoints"""
    is_correct_username = credentials.username == AUTH_USERNAME
    is_correct_password = credentials.password == AUTH_PASSWORD
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# Модели данных согласно R-TokensStats.json
class RoleStatsModel(BaseModel):
    """Статистика по роли"""
    daily_limit: int
    used_tokens: int
    remaining_tokens: int
    usage_percentage: float
    calls_count: int
    last_call: Optional[str] = None
    wait_budget_count: int = 0

class TotalUsageModel(BaseModel):
    """Общее использование"""
    total_limit: int
    total_used: int
    total_remaining: int
    overall_percentage: float

class BudgetStatusModel(BaseModel):
    """Статус бюджета"""
    status: str  # healthy, warning, critical
    roles_exhausted: List[str]
    roles_at_risk: List[str] 
    next_reset: str

class MetadataModel(BaseModel):
    """Метаданные ответа"""
    generated_at: str
    correlation_id: str
    query_time_ms: float = 0.0

class TokensStatsResponse(BaseModel):
    """Полный ответ согласно R-TokensStats.json"""
    date: str
    stats_by_role: Dict[str, RoleStatsModel]
    total_usage: TotalUsageModel
    budget_status: BudgetStatusModel
    metadata: MetadataModel

# Legacy модели для совместимости
class TokenStatsResponse(BaseModel):
    role: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    daily_limit: int
    daily_used: int
    daily_remaining: int

class BudgetSummaryResponse(BaseModel):
    total_daily_limit: int
    total_daily_used: int
    total_daily_remaining: int
    roles_summary: Dict[str, Dict[str, Any]]

# Основной endpoint согласно E15-FIXES
@router.get("/tokens", response_model=TokensStatsResponse)
async def get_tokens_stats(
    request: Request,
    username: str = Depends(verify_credentials),
    debug: bool = Query(False, description="Включить расширенные логи для диагностики")
):
    """
    Получает статистику токенов по ролям с данными для E15 Go/No-Go проверки.
    Endpoint для исправления 401 ошибки из E15_TEST_ACCEPT_COMPREHENSIVE.md
    
    Args:
        request: HTTP запрос
        username: Авторизованный пользователь
        
    Returns:
        TokensStatsResponse: Статистика согласно R-TokensStats.json схеме
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()
    
    log.info(
        event="admin_tokens_stats_start",
        env=get_env(),
        component="admin_api", 
        agent_role="System",
        run_id=correlation_id,
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_path": str(request.url.path),
            "username": username
        }
    )
    
    try:
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
        engine = create_engine(DATABASE_URL)
        
        current_date = datetime.now(timezone.utc)
        date_str = current_date.strftime("%Y-%m-%d")
        
        with engine.connect() as conn:
            # Диагностика схемы таблицы при включенном debug
            if debug:
                try:
                    pragma = conn.execute(text("PRAGMA table_info(token_stats)"))
                    cols = [row[1] for row in pragma.fetchall()]
                    log.info(
                        event="tokens_debug_schema",
                        env=get_env(),
                        component="admin_api",
                        agent_role="System",
                        correlation_id=correlation_id,
                        kv={"columns": cols}
                    )
                except Exception as e:
                    log.warn(
                        event="tokens_debug_schema_error",
                        env=get_env(),
                        component="admin_api",
                        agent_role="System",
                        correlation_id=correlation_id,
                        kv={"err": str(e)}
                    )
            # Получаем статистику по ролям
            roles_query = text("""
                SELECT 
                    agent_role,
                    SUM(COALESCE(input_tokens,0) + COALESCE(output_tokens,0)) as used_tokens,
                    SUM(COALESCE(total_calls,0)) as calls_count
                FROM token_stats 
                WHERE date = DATE('now')
                GROUP BY agent_role
                ORDER BY agent_role
            """)
            
            roles_result = conn.execute(roles_query)
            stats_by_role = {}
            total_limit = 0
            total_used = 0
            roles_at_risk = []
            roles_exhausted = []
            
            # Обрабатываем каждую роль
            for row in roles_result:
                role = row[0]
                used_tokens = int(row[1] or 0)
                calls_count = int(row[2] or 0)
                # Дефолтные лимиты, т.к. в схеме их нет
                default_limits = {"Dev": 1400, "Architect": 800, "QA": 800, "Scribe": 800, "Maintainer": 800}
                daily_limit = default_limits.get(role, 800)
                last_call = None
                
                remaining_tokens = max(0, daily_limit - used_tokens)
                usage_percentage = (used_tokens / daily_limit * 100) if daily_limit > 0 else 0
                
                # Определяем статус риска
                if usage_percentage >= 100:
                    roles_exhausted.append(role)
                elif usage_percentage > 80:
                    roles_at_risk.append(role)
                
                stats_by_role[role] = RoleStatsModel(
                    daily_limit=daily_limit,
                    used_tokens=used_tokens,
                    remaining_tokens=remaining_tokens,
                    usage_percentage=round(usage_percentage, 2),
                    calls_count=calls_count,
                    last_call=last_call.isoformat() if last_call else None,
                    wait_budget_count=0  # TODO: реализовать подсчет WAIT_BUDGET
                )
                
                total_limit += daily_limit
                total_used += used_tokens
            
            # Добавляем роли по умолчанию, если их нет в БД
            default_roles = ["Architect", "Dev", "QA", "Scribe", "Maintainer"]
            for role in default_roles:
                if role not in stats_by_role:
                    daily_limit = 1400 if role == "Dev" else 800
                    stats_by_role[role] = RoleStatsModel(
                        daily_limit=daily_limit,
                        used_tokens=0,
                        remaining_tokens=daily_limit,
                        usage_percentage=0.0,
                        calls_count=0,
                        last_call=None,
                        wait_budget_count=0
                    )
                    total_limit += daily_limit
        
        total_remaining = max(0, total_limit - total_used)
        overall_percentage = (total_used / total_limit * 100) if total_limit > 0 else 0
        
        # Определяем общий статус бюджета
        if roles_exhausted:
            budget_status = "critical"
        elif roles_at_risk:
            budget_status = "warning" 
        else:
            budget_status = "healthy"
        
        # Время следующего сброса (полночь UTC)
        next_reset = current_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        
        query_time = (time.time() - start_time) * 1000
        
        response = TokensStatsResponse(
            date=date_str,
            stats_by_role=stats_by_role,
            total_usage=TotalUsageModel(
                total_limit=total_limit,
                total_used=total_used,
                total_remaining=total_remaining,
                overall_percentage=round(overall_percentage, 2)
            ),
            budget_status=BudgetStatusModel(
                status=budget_status,
                roles_exhausted=roles_exhausted,
                roles_at_risk=roles_at_risk,
                next_reset=next_reset.isoformat()
            ),
            metadata=MetadataModel(
                generated_at=current_date.isoformat(),
                correlation_id=correlation_id,
                query_time_ms=round(query_time, 1)
            )
        )
        
        log.info(
            event="admin_tokens_stats_success",
            env=get_env(),
            component="admin_api",
            agent_role="System", 
            run_id=correlation_id,
            correlation_id=correlation_id,
            kv={
                "method": request.method,
                "url_path": str(request.url.path),
                "status": 200,
                "duration_ms": round(query_time, 1),
                "roles_count": len(stats_by_role),
                "budget_status": budget_status
            }
        )
        
        return response
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        
        log.error(
            event="admin_tokens_stats_error",
            env=get_env(),
            component="admin_api",
            agent_role="System",
            run_id=correlation_id,
            correlation_id=correlation_id,
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
            detail=f"Failed to get tokens statistics: {str(e)}",
            headers={
                "x-correlation-id": correlation_id,
                "error_code": "TOKENS_STATS_ERROR"
            }
        )


# Legacy endpoint для совместимости
@router.get("/tokens/stats", response_model=List[TokenStatsResponse])
async def get_token_stats(
    request: Request,
    username: str = Depends(verify_credentials),
    debug: bool = Query(False, description="Включить расширенные логи для диагностики")
):
    """
    Получает детализированную статистику использования токенов по ролям и моделям.
    
    Args:
        request: HTTP запрос
        
    Returns:
        List[TokenStatsResponse]: Список статистики по ролям и моделям
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
        }
    )
    
    try:
        # Получаем DATABASE_URL из переменных окружения
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
        engine = create_engine(DATABASE_URL)
        
        # Получаем статистику токенов из таблицы token_stats
        # В реальной реализации здесь будет более сложный запрос с агрегацией
        # и получением лимитов из настроек
        with engine.connect() as conn:
            # Диагностика схемы таблицы при включенном debug
            if debug:
                try:
                    pragma = conn.execute(text("PRAGMA table_info(token_stats)"))
                    cols = [row[1] for row in pragma.fetchall()]
                    log.info(
                        event="tokens_debug_schema",
                        env=get_env(),
                        component="admin_api",
                        agent_role="System",
                        correlation_id=correlation_id,
                        kv={"columns": cols}
                    )
                except Exception as e:
                    log.warn(
                        event="tokens_debug_schema_error",
                        env=get_env(),
                        component="admin_api",
                        agent_role="System",
                        correlation_id=correlation_id,
                        kv={"err": str(e)}
                    )
            result = conn.execute(
                text("""
                    SELECT 
                        agent_role as role,
                        model,
                        SUM(COALESCE(input_tokens,0)) as input_tokens,
                        SUM(COALESCE(output_tokens,0)) as output_tokens
                    FROM token_stats 
                    GROUP BY agent_role, model
                    ORDER BY agent_role, model
                """)
            )
            token_stats: List[TokenStatsResponse] = []
            default_limits = {"Dev": 1400, "Architect": 800, "QA": 800, "Scribe": 800, "Maintainer": 800}
            for row in result:
                role = row[0]
                model = row[1]
                input_tokens = int(row[2] or 0)
                output_tokens = int(row[3] or 0)
                total_tokens = input_tokens + output_tokens
                daily_limit = default_limits.get(role, 800)
                daily_used = total_tokens
                daily_remaining = max(0, daily_limit - daily_used)
                token_stats.append(
                    TokenStatsResponse(
                        role=role,
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        cost=0.0,
                        daily_limit=daily_limit,
                        daily_used=daily_used,
                        daily_remaining=daily_remaining
                    )
                )
        
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
                "records_returned": len(token_stats)
            }
        )
        
        return token_stats
        
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
            detail=f"Failed to get token stats: {str(e)}",
            headers={
                "x-correlation-id": correlation_id,
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get("/tokens/summary", response_model=BudgetSummaryResponse)
async def get_budget_summary(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """
    Получает сводку по бюджету токенов.
    
    Args:
        request: HTTP запрос
        
    Returns:
        BudgetSummaryResponse: Сводка по бюджету
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
        }
    )
    
    try:
        # Получаем DATABASE_URL из переменных окружения
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
        engine = create_engine(DATABASE_URL)
        
        # Получаем общую сводку по бюджету
        with engine.connect() as conn:
            # Общая сумма
            total_result = conn.execute(
                text("""
                    SELECT 
                        SUM(daily_limit) as total_daily_limit,
                        SUM(total_tokens) as total_daily_used
                    FROM (
                        SELECT 
                            agent_role,
                            MAX(COALESCE(daily_limit,0)) as daily_limit,
                            SUM(COALESCE(input_tokens,0) + COALESCE(output_tokens,0)) as total_tokens
                        FROM token_stats 
                        GROUP BY agent_role
                    )
                """)
            )
            total_row = total_result.fetchone()
            
            total_daily_limit = total_row[0] or 0
            total_daily_used = total_row[1] or 0
            total_daily_remaining = max(0, total_daily_limit - total_daily_used)
            
            # Сводка по ролям
            roles_result = conn.execute(
                text("""
                    SELECT 
                        agent_role,
                        MAX(COALESCE(daily_limit,0)) as daily_limit,
                        SUM(COALESCE(input_tokens,0) + COALESCE(output_tokens,0)) as daily_used
                    FROM token_stats 
                    GROUP BY agent_role
                    ORDER BY agent_role
                """)
            )
            
            roles_summary = {}
            for row in roles_result:
                role = row[0]
                daily_limit = row[1] or 0
                daily_used = row[2] or 0
                daily_remaining = max(0, daily_limit - daily_used)
                percentage_used = (daily_used / daily_limit * 100) if daily_limit > 0 else 0
                
                roles_summary[role] = {
                    "daily_limit": daily_limit,
                    "daily_used": daily_used,
                    "daily_remaining": daily_remaining,
                    "percentage_used": round(percentage_used, 2)
                }
        
        summary = BudgetSummaryResponse(
            total_daily_limit=total_daily_limit,
            total_daily_used=total_daily_used,
            total_daily_remaining=total_daily_remaining,
            roles_summary=roles_summary
        )
        
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
            }
        )
        
        return summary
        
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
            detail=f"Failed to get budget summary: {str(e)}",
            headers={
                "x-correlation-id": correlation_id,
                "error_code": "INTERNAL_ERROR"
            }
        )
