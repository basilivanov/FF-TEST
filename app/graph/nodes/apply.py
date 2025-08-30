#!/usr/bin/env python3
"""
Узел Apply для графа G1.
"""

import asyncio
import os
import sqlite3
import structlog
from typing import Dict, Any
from app.orchestrator.apply import ArtifactApplier
from app.graph.types import RunCtx
from app.db.guard import get_db_connection_string
from langgraph.graph import END

# Настройка логгера
logger = structlog.get_logger()

async def apply_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Вход в узел Apply", state=state)
    """
    Узел Apply - применяет артефакты в целевой системе.
    
    Args:
        state (Dict[str, Any]): Состояние графа
        
    Returns:
        Dict[str, Any]: Обновленное состояние графа
    """
    try:
        run_ctx = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")
        
        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id
        run_id = run_ctx.run_id

        logger.info(
            "apply_node_started",
            component="graph",
            agent_role="Apply",
            run_id=run_id,
            feature_id=feature_id,
            correlation_id=correlation_id
        )
        
        # Получаем артефакты из состояния графа
        artifacts_dir = state.get("artifacts_dir")
        artifact_manifest = state.get("artifact_manifest")

        if not artifacts_dir or not artifact_manifest:
            logger.error(
                "apply_node_missing_artifacts",
                component="graph",
                agent_role="Apply",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "apply_failed",
                "result": "Missing artifacts or manifest from previous nodes"
            }
        
        # Создаем applier
        applier = ArtifactApplier()
        
        # Применяем артефакты
        try:
            success = applier.apply_artifact(artifact_manifest, artifacts_dir)
            
            if success:
                # Обновляем статус feature в БД
                _update_feature_status(feature_id, "DONE")
                
                logger.info(
                    "apply_node_finished",
                    component="graph",
                    agent_role="Apply",
                    run_id=run_id,
                    feature_id=feature_id,
                    correlation_id=correlation_id,
                    apply_result="SUCCESS"
                )
                
                return END # Завершаем граф
            else:
                logger.info(
                    "apply_node_finished",
                    component="graph",
                    agent_role="Apply",
                    run_id=run_id,
                    feature_id=feature_id,
                    correlation_id=correlation_id,
                    apply_result="FAILED"
                )
                
                return {
                    "status": "apply_failed",
                    "result": "Artifacts application failed"
                }
                
        except Exception as e:
            logger.error(
                "apply_node_processing_failed",
                component="graph",
                agent_role="Apply",
                err_type=type(e).__name__,
                error=str(e),
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "apply_failed",
                "result": f"Error during artifact application: {str(e)}"
            }
            
    except Exception as e:
        logger.error(
            "apply_node_failed",
            component="graph",
            agent_role="Apply",
            err_type=type(e).__name__,
            error=str(e),
            run_id=state.get("run_ctx").run_id if state.get("run_ctx") else "unknown"
        )
        return {
            "status": "apply_failed",
            "result": f"Apply node failed: {str(e)}"
        }

def _update_feature_status(feature_id: str, status: str):
    """Обновляет статус feature в БД."""
    try:
        db_url = get_db_connection_string()
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "UPDATE features SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, feature_id)
                )
                conn.commit()
                
                logger.info(
                    "feature_status_updated",
                    component="graph",
                    agent_role="Apply",
                    feature_id=feature_id,
                    status=status
                )
    except Exception as e:
        logger.error(
            "feature_status_update_failed",
            component="graph",
            agent_role="Apply",
            feature_id=feature_id,
            status=status,
            error=str(e)
        )