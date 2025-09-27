#!/usr/bin/env python3
"""
Узел Apply для графа G1.
"""

import asyncio
import os
import sqlite3
import shutil
import structlog
from typing import Dict, Any
from app.orchestrator.apply import ArtifactApplier
from app.graph.types import RunCtx
from app.db.guard import get_db_connection_string
from app.services.git_integration import GitIntegrationService
from langgraph.graph import END

# Настройка логгера
logger = structlog.get_logger()


class GitOpsArtifactApplier:
    """GitOps-aware artifact applier that applies artifacts to worktree instead of main."""
    
    def __init__(self, git_service: GitIntegrationService, branch_name: str):
        self.git_service = git_service
        self.branch_name = branch_name
        self.worktree_path = os.path.join(git_service.worktrees_root, branch_name)
    
    def apply_artifact(self, manifest: Dict[str, Any], artifacts_dir: str) -> bool:
        """
        Apply validated artifact to worktree.
        
        Args:
            manifest (Dict[str, Any]): Validated manifest
            artifacts_dir (str): The temporary directory containing the generated artifacts
            
        Returns:
            bool: True if applied successfully to worktree
        """
        try:
            package_id = manifest.get("package_contract", {}).get("package_id", "unknown")
            files_to_apply = manifest.get("files", [])
            
            logger.info(
                "gitops_artifact_apply_started",
                component="orchestrator",
                agent_role="GitOpsApply",
                package_id=package_id,
                files_count=len(files_to_apply),
                artifacts_dir=artifacts_dir,
                worktree_path=self.worktree_path,
                branch=self.branch_name
            )
            
            if not os.path.exists(self.worktree_path):
                raise ValueError(f"Worktree path does not exist: {self.worktree_path}")
            
            # Копируем файлы из временного каталога в worktree
            for file_name in files_to_apply:
                source_path = os.path.join(artifacts_dir, file_name)
                
                # Определяем целевой путь в worktree
                target_path = os.path.join(self.worktree_path, file_name)
                
                # Создаем необходимые директории в worktree
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # Копируем файл в worktree
                shutil.copy2(source_path, target_path)
                
                logger.info(
                    "gitops_file_applied",
                    component="orchestrator",
                    agent_role="GitOpsApply",
                    source=source_path,
                    target=target_path,
                    branch=self.branch_name
                )
            
            # Добавляем все изменения в git в worktree
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "add", "."], 
                    cwd=self.worktree_path, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                logger.info("gitops_changes_staged", branch=self.branch_name)
            except subprocess.CalledProcessError as e:
                logger.warning("gitops_staging_failed", error=e.stderr, branch=self.branch_name)
            
            logger.info(
                "gitops_artifact_apply_finished",
                component="orchestrator",
                agent_role="GitOpsApply",
                package_id=package_id,
                status="SUCCESS",
                branch=self.branch_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "gitops_artifact_apply_failed",
                component="orchestrator",
                agent_role="GitOpsApply",
                error=str(e),
                branch=self.branch_name,
                stack=True
            )
            return False

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
        
        # Проверяем результат QA — применяем только при PASS
        qa_result = state.get("qa_result")
        if qa_result and qa_result != "PASS":
            logger.warning(
                "apply_blocked_by_failed_tests",
                component="graph",
                agent_role="Apply",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id,
                qa_result=qa_result,
            )
            return {
                "status": "apply_blocked",
                "result": "Apply blocked: QA tests not passing",
                "qa_result": qa_result,
            }

        # Инициализируем GitOps интеграцию
        git_service = GitIntegrationService()
        
        # Получаем информацию о feature из БД для создания ветки
        feature_info = _get_feature_info(feature_id)
        feature_title = feature_info.get("title", f"Feature {feature_id}")
        
        # GitOps workflow
        git_branch = None
        pr_url = None
        commit_sha = None
        merge_result = None
        success = False
        
        try:
            # 1. Создаем ветку feature и worktree
            git_branch = git_service.create_feature_branch(
                feature_id, feature_title, correlation_id
            )
            logger.info("GitOps: feature branch created", branch=git_branch)
            
            # 2. Применяем артефакты В worktree (вместо прямого копирования в main)
            worktree_applier = GitOpsArtifactApplier(git_service, git_branch)
            success = worktree_applier.apply_artifact(artifact_manifest, artifacts_dir)
            
            if success:
                logger.info("GitOps: artifacts applied to worktree", branch=git_branch)
                
                # 3. Создаем коммит с артефактами в worktree
                commit_file = git_service.ensure_unique_commit(feature_id, correlation_id)
                if commit_file:
                    logger.info("GitOps: changes committed to worktree", file=commit_file)
                
                # 4. Создаем PR из worktree
                pr_result = git_service.create_pull_request(
                    git_branch, feature_id, feature_title, correlation_id
                )
                pr_url = pr_result.get("pr_url")
                pr_number = pr_result.get("pr_number")
                commit_sha = pr_result.get("head_sha", commit_sha)
                
                logger.info("GitOps: PR created", pr_url=pr_url, pr_number=pr_number)
                
                # 5. Автоматически мерджим PR (в TEST среде)
                if pr_number and commit_sha:
                    merge_result = git_service.merge_pull_request(
                        feature_id, pr_number, commit_sha, correlation_id
                    )
                    logger.info("GitOps: PR merged", merge_result=merge_result)
                    success = merge_result.get("merged", False)
                    
        except Exception as e:
            logger.error("GitOps workflow failed", error=str(e), stack=True)
            # Fallback: используем старый подход только если GitOps полностью сломан
            applier = ArtifactApplier()
            success = applier.apply_artifact(artifact_manifest, artifacts_dir)
            logger.warning("Applied artifacts via fallback (non-GitOps) method")
        
        # Обновляем статус feature в БД с GitOps данными
        _update_feature_status_with_gitops(
            feature_id, "DONE" if success else "FAILED", git_branch, pr_url, commit_sha, 
            merge_result.get("merged", False) if merge_result else False,
            merge_result.get("merge_commit_sha") if merge_result else None,
            correlation_id
        )
        
        if success:
            logger.info(
                "apply_node_finished",
                component="graph",
                agent_role="Apply",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id,
                apply_result="SUCCESS",
                git_branch=git_branch,
                pr_url=pr_url
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

def _get_feature_info(feature_id: str) -> Dict[str, Any]:
    """Получает информацию о feature из БД."""
    try:
        db_url = get_db_connection_string()
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT id, title, intent_json FROM features WHERE id = ?",
                    (feature_id,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                else:
                    return {"title": f"Feature {feature_id}"}
    except Exception as e:
        logger.error(
            "feature_info_fetch_failed",
            component="graph",
            agent_role="Apply",
            feature_id=feature_id,
            error=str(e)
        )
        return {"title": f"Feature {feature_id}"}

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

def _update_feature_status_with_gitops(
    feature_id: str, status: str, git_branch: str = None, pr_url: str = None, 
    commit_sha: str = None, merged: bool = False, merged_sha: str = None, 
    correlation_id: str = None
):
    """Обновляет статус feature в БД с GitOps данными."""
    try:
        db_url = get_db_connection_string()
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """UPDATE features SET 
                       status = ?, 
                       git_branch = ?, 
                       pr_url = ?, 
                       commit_sha = ?, 
                       merged = ?, 
                       merged_sha = ?, 
                       last_corr_id = ?,
                       updated_at = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    (status, git_branch, pr_url, commit_sha, merged, merged_sha, correlation_id, feature_id)
                )
                conn.commit()
                
                logger.info(
                    "feature_gitops_updated",
                    component="graph",
                    agent_role="Apply",
                    feature_id=feature_id,
                    status=status,
                    git_branch=git_branch,
                    pr_url=pr_url,
                    merged=merged
                )
    except Exception as e:
        logger.error(
            "feature_gitops_update_failed",
            component="graph",
            agent_role="Apply",
            feature_id=feature_id,
            status=status,
            error=str(e)
        )