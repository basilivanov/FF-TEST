#!/usr/bin/env python3
"""CI API endpoints для GitHub webhook'ов и статусов."""

import os
import json
import hmac
import hashlib
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from app.logging_helpers import log, get_env, generate_correlation_id

router = APIRouter(prefix="/api/v1/ci", tags=["CI"])
security = HTTPBasic()


class CIStatusRequest(BaseModel):
    """Схема запроса CI статуса."""

    context: str  # lint, tests, build, smoke
    state: str  # pending, success, failure, error
    target_url: str = ""
    description: str = ""
    correlation_id: str = ""


def _log(level: str, event: str, correlation_id: str, task_id: str, **kv: Any) -> None:
    log_method = getattr(log, level)
    log_method(
        event=event,
        env=get_env(),
        component="ci_api",
        agent_role="Ops",
        run_id=correlation_id,
        task_id=task_id,
        correlation_id=correlation_id,
        kv=kv,
    )


def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка Basic Auth для CI endpoints."""

    expected_user = os.getenv("CI_HOOK_USER", "ops")
    expected_pass = os.getenv("CI_HOOK_PASS", "ops123")

    if credentials.username != expected_user or credentials.password != expected_pass:
        raise HTTPException(
            status_code=401,
            detail="Invalid CI credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


def verify_github_webhook(
    request: Request,
    body: bytes,
    correlation_id: str,
    task_id: str,
) -> None:
    """Проверка GitHub webhook signature."""

    github_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not github_secret:
        _log("warning", "github_webhook_no_secret", correlation_id, task_id)
        return

    signature_header = request.headers.get("X-Hub-Signature-256", "")
    if not signature_header.startswith("sha256="):
        _log("warning", "github_webhook_signature_format_invalid", correlation_id, task_id)
        raise HTTPException(status_code=401, detail="Invalid signature format")

    expected_signature = signature_header[7:]
    actual_signature = hmac.new(github_secret.encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, actual_signature):
        _log("warning", "github_webhook_signature_mismatch", correlation_id, task_id)
        raise HTTPException(status_code=401, detail="Invalid signature")


@router.post("/webhook")
async def github_webhook(request: Request):
    """GitHub webhook endpoint."""

    correlation_id = request.headers.get("x-correlation-id", generate_correlation_id())
    task_id = str(uuid.uuid4())

    try:
        body = await request.body()
        verify_github_webhook(request, body, correlation_id, task_id)

        payload = json.loads(body.decode())
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        _log(
            "info",
            "github_webhook_received",
            correlation_id,
            task_id,
            event_type=event_type,
            action=payload.get("action", ""),
            repository=payload.get("repository", {}).get("full_name", ""),
            sender=payload.get("sender", {}).get("login", ""),
        )

        if event_type == "pull_request":
            await handle_pull_request_event(payload, correlation_id, task_id)
        elif event_type == "push":
            await handle_push_event(payload, correlation_id, task_id)
        elif event_type in {"check_run", "check_suite"}:
            await handle_check_event(payload, correlation_id, task_id)
        else:
            _log("info", "github_webhook_ignored", correlation_id, task_id, event_type=event_type)

        return {"status": "ok", "event": event_type}

    except json.JSONDecodeError:
        _log("warning", "github_webhook_invalid_json", correlation_id, task_id)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log(
            "error",
            "github_webhook_error",
            correlation_id,
            task_id,
            err_type=type(exc).__name__,
            err_msg=str(exc),
        )
        raise HTTPException(status_code=500, detail="Webhook processing failed") from exc


@router.post("/status")
async def ci_status(
    status_request: CIStatusRequest,
    credentials: HTTPBasicCredentials = Depends(verify_basic_auth),
):
    """CI статус endpoint для обновления статусов PR."""

    correlation_id = status_request.correlation_id or generate_correlation_id()
    task_id = str(uuid.uuid4())

    try:
        _log(
            "info",
            "ci_status_received",
            correlation_id,
            task_id,
            context=status_request.context,
            state=status_request.state,
            target_url=status_request.target_url,
            user=credentials.username,
        )

        response = {
            "status": "ok",
            "context": status_request.context,
            "state": status_request.state,
            "updated_at": "2025-09-17T14:48:00Z",
        }

        _log("info", "ci_status_processed", correlation_id, task_id, result_state=status_request.state)
        return response

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log(
            "error",
            "ci_status_error",
            correlation_id,
            task_id,
            err_type=type(exc).__name__,
            err_msg=str(exc),
        )
        raise HTTPException(status_code=500, detail="Status update failed") from exc


@router.get("/debug/git-env")
async def debug_git_env():
    """Диагностический endpoint для проверки Git переменных."""

    correlation_id = generate_correlation_id()
    task_id = str(uuid.uuid4())

    git_vars = {}
    for var in [
        "GITHUB_OWNER",
        "GITHUB_REPO",
        "GIT_BASE_BRANCH",
        "GITHUB_APP_ID",
        "GITHUB_APP_INSTALLATION_ID",
        "GITHUB_TOKEN",
    ]:
        value = os.getenv(var)
        git_vars[var] = {"present": value is not None, "length": len(value) if value else 0}

    payload = {
        "git_integration_enabled": os.getenv("GIT_INTEGRATION_ENABLED", "false").lower() == "true",
        "scm_push_enabled": os.getenv("SCM_PUSH_ENABLED", "false").lower() == "true",
        "variables": git_vars,
    }

    _log("info", "ci_debug_git_env", correlation_id, task_id, **payload)
    return payload


async def handle_pull_request_event(
    payload: Dict[str, Any],
    correlation_id: str,
    task_id: str,
) -> None:
    """Обработка событий pull request."""

    _log(
        "info",
        "github_pr_event",
        correlation_id,
        task_id,
        action=payload.get("action", ""),
        pr_number=payload.get("number"),
    )


async def handle_push_event(payload: Dict[str, Any], correlation_id: str, task_id: str) -> None:
    """Обработка событий push."""

    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ""

    _log("info", "github_push_event", correlation_id, task_id, ref=ref, branch=branch)


async def handle_check_event(payload: Dict[str, Any], correlation_id: str, task_id: str) -> None:
    """Обработка событий check_run/check_suite."""

    conclusion = payload.get("check_run", {}).get("conclusion") or payload.get("check_suite", {}).get("conclusion")
    _log("info", "github_check_event", correlation_id, task_id, conclusion=conclusion)
