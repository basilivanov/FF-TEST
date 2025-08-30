from __future__ import annotations

import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Импортируем logging_helpers
from app.logging_helpers import log, get_env, generate_correlation_id

# Database setup - moved to function to allow runtime changes
def get_database_url():
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")

def get_engine():
    """Get database engine."""
    return create_engine(get_database_url())

def get_session_local():
    """Get SessionLocal for current database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

router = APIRouter(prefix="/api/v1/docs")

# Pydantic модели
class DocStatusResponse(BaseModel):
    doc_name: str
    version: str
    content_hash: str
    updated_at: str

class DocsStatusResponse(BaseModel):
    docs: List[DocStatusResponse]

class RebuildResponse(BaseModel):
    status: str
    message: str
    docs_updated: int

# Вспомогательные функции
def get_db():
    """Получает сессию базы данных."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_correlation_id(request) -> str:
    """Получает correlation_id из заголовков запроса."""
    return request.headers.get("x-correlation-id", generate_correlation_id())

def log_api_call_start(request, correlation_id: str, **kwargs):
    """Логирует начало API вызова."""
    log.info(
        event="api_call_start",
        env=get_env(),
        component="api",
        agent_role="DocsAPI",
        run_id=correlation_id,
        task_id=str(generate_correlation_id()),
        correlation_id=correlation_id,
        kv={
            "method": request.method,
            "url_host": request.url.hostname or "localhost",
            "url_path": str(request.url.path),
            **kwargs
        }
    )

def log_api_call_end(request, correlation_id: str, status_code: int, duration_ms: float, **kwargs):
    """Логирует завершение API вызова."""
    log.info(
        event="api_call_end",
        env=get_env(),
        component="api",
        agent_role="DocsAPI",
        run_id=correlation_id,
        task_id=str(generate_correlation_id()),
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

def calculate_file_hash(file_path: str) -> str:
    """Вычисляет хэш файла."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return "file_not_found"

# Эндпоинты API
@router.get("/status", response_model=DocsStatusResponse)
async def get_docs_status(request: Request):
    """
    Получает статус документов.
    
    Returns:
        DocsStatusResponse: Список документов с их статусами
    """
    start_time = datetime.now()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(request, correlation_id)
    
    try:
        # Проверяем существование таблицы doc_registry
        with get_engine().connect() as conn:
            # Получаем список документов из реестра
            result = conn.execute(text("""
                SELECT doc_name, version, content_hash, updated_at
                FROM doc_registry
                ORDER BY doc_name
            """))
            
            docs = []
            for row in result:
                docs.append({
                    "doc_name": row[0],
                    "version": row[1],
                    "content_hash": row[2],
                    "updated_at": row[3].isoformat() if hasattr(row[3], 'isoformat') else str(row[3])
                })
            
            # Логируем успешное завершение вызова
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            log_api_call_end(request, correlation_id, status_code=200, duration_ms=duration_ms)
            
            return {"docs": docs}
            
    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="DocsAPI",
            run_id=correlation_id,
            task_id=str(generate_correlation_id()),
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
            detail="Failed to get docs status",
            headers={"error_code": "INTERNAL_ERROR"}
        )

@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_docs(request: Request):
    """
    Пересобирает документацию.
    
    Returns:
        RebuildResponse: Результат пересборки
    """
    start_time = datetime.now()
    correlation_id = get_correlation_id(request)
    
    # Логируем начало вызова
    log_api_call_start(request, correlation_id)
    
    try:
        # В реальной реализации здесь будет логика пересборки документации
        # Для демонстрации просто обновляем хэши документов в реестре
        docs_updated = 0
        
        with get_engine().connect() as conn:
            # Получаем все документы из реестра
            result = conn.execute(text("""
                SELECT doc_name
                FROM doc_registry
                ORDER BY doc_name
            """))
            
            docs = result.fetchall()
            
            # Обновляем хэши для каждого документа
            for doc_row in docs:
                doc_name = doc_row[0]
                doc_path = doc_name
                
                # Вычисляем новый хэш файла
                new_hash = calculate_file_hash(doc_path)
                
                # Обновляем запись в реестре
                conn.execute(text("""
                    UPDATE doc_registry
                    SET content_hash = :new_hash, updated_at = datetime('now')
                    WHERE doc_name = :doc_name
                """), {
                    "new_hash": new_hash,
                    "doc_name": doc_name
                })
                
                docs_updated += 1
                
                # Логируем обновление документа
                log.info(
                    event="doc_updated",
                    env=get_env(),
                    component="docs",
                    agent_role="DocsAPI",
                    run_id=correlation_id,
                    task_id=str(generate_correlation_id()),
                    correlation_id=correlation_id,
                    kv={
                        "doc_name": doc_name,
                        "content_hash": new_hash
                    }
                )
            
            conn.commit()
        
        # Логируем успешное завершение вызова
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        log_api_call_end(request, correlation_id, status_code=200, duration_ms=duration_ms, docs_updated=docs_updated)
        
        return {
            "status": "success",
            "message": f"Documentation rebuilt successfully. {docs_updated} documents updated.",
            "docs_updated": docs_updated
        }
        
    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="api",
            agent_role="DocsAPI",
            run_id=correlation_id,
            task_id=str(generate_correlation_id()),
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
            detail="Failed to rebuild documentation",
            headers={"error_code": "INTERNAL_ERROR"}
        )