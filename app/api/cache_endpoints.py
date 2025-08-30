#!/usr/bin/env python3
"""
Кешированные endpoints для быстрой загрузки UI.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import time

from app.db.session import get_db
from app.utils.cache import cache, CACHE_TTL, get_cache_key
from app.api.health import check_llm_cli_health
from app.api.orchestrator_v2_endpoints import get_features, get_runs
from app.api.tokens_stats_endpoints import get_tokens_summary

router = APIRouter(prefix="/api/v1/cached")

@router.get("/health/ready")
async def cached_health_ready(db: Session = Depends(get_db)):
    """Кешированная проверка готовности системы"""
    cache_key = get_cache_key("health_ready")
    cached_result = cache.get(cache_key)
    
    if cached_result:
        cached_result["cached"] = True
        cached_result["cache_age"] = time.time() - cached_result.get("_cached_at", 0)
        return cached_result
    
    # Импортируем здесь чтобы избежать циклических импортов
    from app.api.health import check_database_health, check_migrations_health, check_index_files_health
    
    checks = [
        check_database_health(db),
        check_migrations_health(db),  
        check_index_files_health()
    ]
    
    all_healthy = all(check["status"] == "ok" for check in checks)
    result = {
        "status": "ok" if all_healthy else "error",
        "component": "ready", 
        "checks": checks,
        "_cached_at": time.time()
    }
    
    cache.set(cache_key, result, CACHE_TTL["health_ready"])
    result["cached"] = False
    return result

@router.get("/health/deps") 
async def cached_health_deps():
    """Кешированная проверка LLM агентов"""
    cache_key = get_cache_key("health_deps")
    cached_result = cache.get(cache_key)
    
    if cached_result:
        cached_result["cached"] = True
        cached_result["cache_age"] = time.time() - cached_result.get("_cached_at", 0)
        return cached_result
    
    llm_check = check_llm_cli_health()
    result = {
        "status": llm_check["status"],
        "component": "deps",
        "checks": [llm_check],
        "_cached_at": time.time()
    }
    
    cache.set(cache_key, result, CACHE_TTL["health_deps"])
    result["cached"] = False
    return result

@router.get("/features")
async def cached_features(db: Session = Depends(get_db)):
    """Кешированный список фич"""
    cache_key = get_cache_key("features")
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return {"data": cached_result, "cached": True}
    
    features = await get_features(db=db)
    cache.set(cache_key, features, CACHE_TTL["features"])
    return {"data": features, "cached": False}

@router.get("/runs")
async def cached_runs(db: Session = Depends(get_db)):
    """Кешированный список запусков"""
    cache_key = get_cache_key("runs") 
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return {"data": cached_result, "cached": True}
    
    runs = await get_runs(db=db)
    cache.set(cache_key, runs, CACHE_TTL["runs"])
    return {"data": runs, "cached": False}

@router.get("/tokens/summary")
async def cached_tokens_summary(db: Session = Depends(get_db)):
    """Кешированная сводка по токенам"""
    cache_key = get_cache_key("tokens_summary")
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return {"data": cached_result, "cached": True}
    
    summary = await get_tokens_summary(db=db)
    cache.set(cache_key, summary, CACHE_TTL["tokens_summary"])
    return {"data": summary, "cached": False}

@router.delete("/cache")
async def clear_cache():
    """Очистить весь кеш (для отладки)"""
    cache.clear()
    return {"message": "Cache cleared"}

@router.get("/cache/stats")
async def cache_stats():
    """Статистика кеша"""
    stats = cache.stats()
    cache.cleanup_expired()
    return stats