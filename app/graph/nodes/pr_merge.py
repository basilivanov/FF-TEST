#!/usr/bin/env python3
"""
PR Merge node для автоматического мержа PR после успешных CI проверок.
"""

import asyncio
import os
import structlog
import json
from typing import Dict, Any
from app.graph.types import RunCtx
from app.services.git_integration import GitIntegrationService, GitIntegrationError
from app.db.session import get_db
from sqlalchemy import text

# Настройка логгера
logger = structlog.get_logger()

async def pr_merge_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    PR Merge node - мержит PR в основную ветку после успешных CI проверок.
    
    Args:
        state (Dict[str, Any]): Состояние графа
        
    Returns:
        Dict[str, Any]: Обновленное состояние графа с информацией о merge
    """
    try:
        run_ctx = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")

        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id
        run_id = run_ctx.run_id

        logger.info(
            "pr_merge_node_started",
            component="graph",
            agent_role="PRMerge",
            run_id=run_id,
            feature_id=feature_id,
            correlation_id=correlation_id
        )

        # Получаем информацию о PR из состояния графа
        pr_info = state.get("pr_info")
        if not pr_info:
            # Пытаемся получить PR info из базы данных
            db_gen = get_db()
            db = next(db_gen)
            try:
                feature_result = db.execute(
                    text("SELECT pr_url FROM features WHERE id = :feature_id"),
                    {"feature_id": feature_id}
                ).fetchone()
                
                if not feature_result or not feature_result[0]:
                    return {
                        "status": "pr_merge_skipped",
                        "result": "No PR URL found for this feature",
                        "merge_info": None
                    }
                
                # Парсим PR number из URL
                pr_url = feature_result[0]
                try:
                    pr_number = int(pr_url.split('/pull/')[-1])
                    pr_info = {"pr_number": pr_number, "pr_url": pr_url}
                except:
                    return {
                        "status": "pr_merge_failed",
                        "result": f"Could not parse PR number from URL: {pr_url}",
                        "merge_info": None
                    }
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass

        # Инициализируем Git сервис
        git_service = GitIntegrationService()
        
        if not git_service.git_enabled or not git_service.push_enabled:
            logger.warning(
                "git_integration_disabled",
                component="graph",
                agent_role="PRMerge",
                run_id=run_id,
                feature_id=feature_id
            )
            return {
                "status": "pr_merge_skipped",
                "result": "Git integration is disabled",
                "merge_info": None
            }

        try:
            # Получаем head SHA для мержа
            head_sha = pr_info.get("head_sha", "")
            pr_number = pr_info["pr_number"]

            # Выполняем merge PR
            merge_info = git_service.merge_pull_request(
                feature_id=int(feature_id),
                pr_number=pr_number,
                head_sha=head_sha,
                correlation_id=correlation_id
            )
            
            # Обновляем фичу с информацией о merge
            db_gen = get_db()
            db = next(db_gen)
            try:
                db.execute(
                    text("""
                        UPDATE features 
                        SET merged_sha = :merged_sha,
                            updated_at = datetime('now')
                        WHERE id = :feature_id
                    """),
                    {
                        "merged_sha": merge_info.get("merge_commit_sha"),
                        "feature_id": feature_id
                    }
                )
                db.commit()
                
                logger.info(
                    "feature_updated_with_merge_info",
                    component="graph",
                    agent_role="PRMerge",
                    run_id=run_id,
                    feature_id=feature_id,
                    merge_commit_sha=merge_info.get("merge_commit_sha"),
                    merged_at=merge_info.get("merged_at")
                )
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass

            return {
                "status": "pr_merge_completed",
                "result": f"PR #{pr_number} merged successfully",
                "merge_info": merge_info
            }

        except GitIntegrationError as e:
            logger.error(
                "pr_merge_integration_failed",
                component="graph",
                agent_role="PRMerge",
                run_id=run_id,
                feature_id=feature_id,
                error=str(e)
            )
            return {
                "status": "pr_merge_failed",
                "result": f"PR merge failed: {str(e)}",
                "merge_info": None
            }

    except Exception as e:
        logger.error(
            "pr_merge_node_failed",
            component="graph",
            agent_role="PRMerge",
            err_type=type(e).__name__,
            error=str(e),
            run_id=state.get("run_ctx").run_id if state.get("run_ctx") else "unknown"
        )
        return {
            "status": "pr_merge_failed",
            "result": f"PR merge node failed: {str(e)}",
            "merge_info": None
        }