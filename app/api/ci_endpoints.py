#!/usr/bin/env python3
"""
CI API endpoints для GitHub webhook'ов и статусов.
"""

import os
import json
import hmac
import hashlib
import structlog
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ci", tags=["CI"])
security = HTTPBasic()
log = structlog.get_logger()


class CIStatusRequest(BaseModel):
    """Схема запроса CI статуса."""
    context: str  # lint, tests, build, smoke
    state: str   # pending, success, failure, error
    target_url: str = ""
    description: str = ""
    correlation_id: str = ""


def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка Basic Auth для CI endpoints."""
    expected_user = os.getenv("CI_HOOK_USER", "ops")
    expected_pass = os.getenv("CI_HOOK_PASS", "ops123")
    
    correct_username = credentials.username == expected_user
    correct_password = credentials.password == expected_pass
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid CI credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


def verify_github_webhook(request: Request, body: bytes):
    """Проверка GitHub webhook signature."""
    github_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not github_secret:
        log.warning("github_webhook_no_secret", msg="GITHUB_WEBHOOK_SECRET not configured")
        return True  # В TEST среде разрешаем без подписи
    
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid signature format")
    
    expected_signature = signature_header[7:]  # Убираем 'sha256='
    actual_signature = hmac.new(
        github_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True


@router.post("/webhook")
async def github_webhook(request: Request):
    """
    GitHub webhook endpoint для обработки событий.
    """
    try:
        body = await request.body()
        verify_github_webhook(request, body)
        
        payload = json.loads(body.decode())
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        
        log.info(
            "github_webhook_received",
            event_type=event_type,
            action=payload.get("action", ""),
            repository=payload.get("repository", {}).get("full_name", ""),
            sender=payload.get("sender", {}).get("login", "")
        )
        
        # Обработка различных типов событий
        if event_type == "pull_request":
            await handle_pull_request_event(payload)
        elif event_type == "push":
            await handle_push_event(payload)
        elif event_type == "check_run" or event_type == "check_suite":
            await handle_check_event(payload)
        else:
            log.info("github_webhook_ignored", event_type=event_type)
        
        return {"status": "ok", "event": event_type}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        log.error("github_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/status")
async def ci_status(
    status_request: CIStatusRequest,
    credentials: HTTPBasicCredentials = Depends(verify_basic_auth)
):
    """
    CI статус endpoint для обновления статусов PR.
    """
    try:
        log.info(
            "ci_status_received",
            context=status_request.context,
            state=status_request.state,
            correlation_id=status_request.correlation_id,
            user=credentials.username
        )
        
        # Здесь можно добавить логику обновления статусов в БД
        # и уведомление GitHub через API
        
        return {
            "status": "ok",
            "context": status_request.context,
            "state": status_request.state,
            "updated_at": "2025-09-17T14:48:00Z"
        }
        
    except Exception as e:
        log.error("ci_status_error", error=str(e))
        raise HTTPException(status_code=500, detail="Status update failed")


@router.get("/debug/git-env")
async def debug_git_env():
    """
    Диагностический endpoint для проверки Git переменных.
    """
    git_vars = {}
    
    for var in ["GITHUB_OWNER", "GITHUB_REPO", "GIT_BASE_BRANCH", 
                "GITHUB_APP_ID", "GITHUB_APP_INSTALLATION_ID", "GITHUB_TOKEN"]:
        value = os.getenv(var)
        git_vars[var] = {
            "present": value is not None,
            "length": len(value) if value else 0
        }
    
    return {
        "git_integration_enabled": os.getenv("GIT_INTEGRATION_ENABLED", "false").lower() == "true",
        "scm_push_enabled": os.getenv("SCM_PUSH_ENABLED", "false").lower() == "true",
        "variables": git_vars
    }


async def handle_pull_request_event(payload: Dict[str, Any]):
    """Обработка событий pull request."""
    action = payload.get("action", "")
    pr_number = payload.get("number", 0)
    
    log.info("github_pr_event", action=action, pr_number=pr_number)
    
    # Здесь можно добавить логику для:
    # - Автоматического мержа при успешных проверках
    # - Обновления статуса фичи в БД
    # - Запуска дополнительных проверок


async def handle_push_event(payload: Dict[str, Any]):
    """Обработка событий push."""
    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ""
    
    log.info("github_push_event", ref=ref, branch=branch)


async def handle_check_event(payload: Dict[str, Any]):
    """Обработка событий check_run/check_suite."""
    conclusion = payload.get("check_run", {}).get("conclusion") or \
                payload.get("check_suite", {}).get("conclusion")
    
    log.info("github_check_event", conclusion=conclusion)