#!/usr/bin/env python3
"""
Узел Gate для графа G1.
"""

import asyncio
import os
import structlog
from typing import Dict, Any
from app.orchestrator.gates import ManifestValidator
from app.graph.types import RunCtx

# Настройка логгера
logger = structlog.get_logger()

async def gate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Узел Gate - валидирует артефакты.
    
    Args:
        state (Dict[str, Any]): Состояние графа
        
    Returns:
        Dict[str, Any]: Обновленное состояние графа
    """
    logger.debug("Вход в узел Gate", state=state)
    try:
        run_ctx = state.get("run_ctx")
        if not run_ctx:
            raise ValueError("Run context not found in state")
        
        feature_id = run_ctx.feature_id
        correlation_id = run_ctx.correlation_id
        run_id = run_ctx.run_id # Получаем run_id

        from app.logging_helpers import get_env
        import uuid
        
        # Получаем данные от узла Dev
        artifacts_dir = state.get("artifacts_dir") # Используем artifacts_dir
        response_text = state.get("response_text", "")
        package_contract_from_architect = state.get("package_contract", {}) # Получаем package_contract от Architect

        logger.info(
            event="job_started",
            env=get_env(),
            component="graph",
            agent_role="Gate",
            run_id=run_id,
            task_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            kv={
                "feature_id": feature_id,
                "graph_node": "gate",
                "artifacts_dir_provided": bool(artifacts_dir),
                "response_text_length": len(response_text) if response_text else 0
            }
        )

        if not artifacts_dir or not response_text:
            logger.error(
                "gate_node_missing_artifacts",
                component="graph",
                agent_role="Gate",
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "REJECT",
                "reason": "REJ_NO_ARTIFACTS",
                "result": "Missing artifacts or response text from Dev node",
                "review_approved": False
            }

        # Создаем валидатор
        validator = ManifestValidator()

        try:
            # 1. Валидация манифеста и package_contract
            manifest = validator.validate_response(response_text, "Dev")

            # 2. Валидация безопасности путей
            if not validator.validate_file_paths(manifest, run_id):
                logger.warning("gate_node_unsafe_paths", run_id=run_id, feature_id=feature_id)
                return {
                    "status": "REJECT",
                    "reason": "REJ_UNSAFE_PATHS",
                    "result": "Unsafe file paths detected in artifact manifest",
                    "review_approved": False
                }

            # 3. Поиск секретов
            detected_secrets = validator.scan_for_secrets(artifacts_dir)
            if detected_secrets:
                logger.warning("gate_node_secret_found", run_id=run_id, feature_id=feature_id, secrets=detected_secrets)
                return {
                    "status": "REJECT",
                    "reason": "REJ_SECRET_FOUND",
                    "result": f"Secrets found in artifacts: {', '.join(detected_secrets)}",
                    "review_approved": False
                }

            logger.info(
                event="job_finished",
                env=get_env(),
                component="graph",
                agent_role="Gate",
                run_id=run_id,
                task_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
                kv={
                    "feature_id": feature_id,
                    "graph_node": "gate",
                    "status": "success",
                    "validation_result": "APPROVED",
                    "manifest_files_count": len(manifest.get("files", [])),
                    "artifacts_dir": artifacts_dir
                }
            )

            return {
                "status": "gate_completed",
                "result": "Gate validation completed",
                "manifest": manifest,
                "artifacts_dir": artifacts_dir,
                "review_approved": True
            }

        except ValueError as e: # Ошибки валидации, которые выбрасывает ManifestValidator
            reason = "REJ_VALIDATION_FAILED"
            if "No manifest found" in str(e):
                reason = "REJ_NO_MANIFEST"
            elif "Artifact manifest schema validation failed" in str(e):
                reason = "REJ_INVALID_MANIFEST_SCHEMA"
            elif "Package contract validation failed" in str(e):
                reason = "REJ_CONTRACT_MISMATCH"

            logger.error(
                "gate_node_validation_failed",
                component="graph",
                agent_role="Gate",
                err_type=type(e).__name__,
                error=str(e),
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "REJECT",
                "reason": reason,
                "result": f"Artifact validation failed: {str(e)}",
                "review_approved": False
            }

        except Exception as e:
            logger.error(
                "gate_node_unexpected_error",
                component="graph",
                agent_role="Gate",
                err_type=type(e).__name__,
                error=str(e),
                run_id=run_id,
                feature_id=feature_id,
                correlation_id=correlation_id
            )
            return {
                "status": "REJECT",
                "reason": "REJ_UNEXPECTED_ERROR",
                "result": f"An unexpected error occurred during gate validation: {str(e)}",
                "review_approved": False
            }

    except Exception as e:
        logger.error(
            "gate_node_failed_initialization",
            component="graph",
            agent_role="Gate",
            err_type=type(e).__name__,
            error=str(e),
            run_id=state.get("run_ctx").run_id if state.get("run_ctx") else "unknown"
        )
        raise

class GateNode:
    def __init__(self):
        pass

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return await gate_node(state)
