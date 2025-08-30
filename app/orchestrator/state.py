#!/usr/bin/env python3
"""
Module for retrieving graph run status.
"""

import os
import sqlite3
from typing import Optional, Dict, Any
import structlog
from app.logging_helpers import log, get_env

# Настройка логгера
logger = structlog.get_logger()

def get_db_connection():
    """Get database connection."""
    database_url = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        return sqlite3.connect(db_path)
    else:
        raise NotImplementedError("Only SQLite database is supported")

def get_graph_run_status(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Получает статус выполнения графа.
    
    Args:
        run_id (str): ID запуска графа
        
    Returns:
        Optional[Dict[str, Any]]: Словарь со статусом графа или None, если граф не найден
        
    Example:
        {
            "run_id": "abc-123",
            "graph": "G1",
            "status": "RUNNING",
            "last_checkpoint": "2023-01-01T10:00:00"
        }
    """
    try:
        # Логируем начало вызова
        logger.info(
            event="get_graph_status_start",
            env=get_env(),
            component="orchestrator",
            agent_role="Orchestrator",
            run_id=run_id,
            kv={}
        )
        
        with get_db_connection() as conn:
            # Получаем статус графа из базы данных
            cursor = conn.execute(
                """
                SELECT run_id, feature_id, graph_name, thread_id, state_json, status, last_checkpoint_at 
                FROM graph_runs 
                WHERE run_id = ?
                """,
                (run_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                # Логируем, что граф не найден
                logger.info(
                    event="get_graph_status_end",
                    env=get_env(),
                    component="orchestrator",
                    agent_role="Orchestrator",
                    run_id=run_id,
                    kv={
                        "status": "NOT_FOUND"
                    }
                )
                return None
            
            # Преобразуем результат в словарь
            last_checkpoint = ""
            if row[6]:
                # Преобразуем datetime в строку
                if hasattr(row[6], 'isoformat'):
                    last_checkpoint = row[6].isoformat()
                else:
                    last_checkpoint = str(row[6])
            
            result = {
                "run_id": row[0],
                "graph": "G1",  # Всегда G1 согласно спецификации
                "status": row[5] or "UNKNOWN",
                "last_checkpoint": last_checkpoint
            }
            
            # Логируем успешное завершение вызова
            logger.info(
                event="get_graph_status_end",
                env=get_env(),
                component="orchestrator",
                agent_role="Orchestrator",
                run_id=run_id,
                kv={
                    "status": result["status"]
                }
            )
            
            return result
            
    except Exception as e:
        # Логируем ошибку
        logger.error(
            event="get_graph_status_error",
            env=get_env(),
            component="orchestrator",
            agent_role="Orchestrator",
            run_id=run_id,
            kv={
                "err_type": type(e).__name__,
                "err_msg": str(e)
            },
            stack=True
        )
        raise