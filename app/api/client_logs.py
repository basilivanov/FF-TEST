#!/usr/bin/env python3
"""
Client-side logging ingestion: allows UI to report errors without crashing silently.
Endpoint: POST /api/v1/logs/client
"""

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
import uuid

from app.logging_helpers import log, get_env, generate_correlation_id
import os, json

router = APIRouter(prefix="/api/v1/logs")
router2 = APIRouter(prefix="/api/v1")


class ClientLogPayload(BaseModel):
    level: str = Field(default="error")
    message: str
    stack: Optional[str] = None
    url: Optional[str] = None
    user_agent: Optional[str] = None
    ui_version: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


async def _ingest(payload: ClientLogPayload, request: Request):
    corr_id = request.headers.get("x-correlation-id") or generate_correlation_id()
    ts = time.time()
    try:
        kv = {
            "ui_log": True,
            "level": payload.level,
            "message": payload.message,
            "stack": payload.stack,
            "url": payload.url,
            "user_agent": payload.user_agent or (request.headers.get("user-agent") if request else None),
            "ui_version": payload.ui_version,
            **(payload.extra or {}),
        }
        # Route by level (stdout)
        level = (payload.level or "error").lower()
        if level in ("debug", "trace"):
            log.debug("ui_client_log", env=get_env(), component="ui", agent_role="UI", run_id=corr_id, task_id=str(uuid.uuid4()), correlation_id=corr_id, kv=kv)
        elif level in ("info",):
            log.info("ui_client_log", env=get_env(), component="ui", agent_role="UI", run_id=corr_id, task_id=str(uuid.uuid4()), correlation_id=corr_id, kv=kv)
        elif level in ("warn", "warning"):
            log.warning("ui_client_log", env=get_env(), component="ui", agent_role="UI", run_id=corr_id, task_id=str(uuid.uuid4()), correlation_id=corr_id, kv=kv)
        else:
            log.error("ui_client_log", env=get_env(), component="ui", agent_role="UI", run_id=corr_id, task_id=str(uuid.uuid4()), correlation_id=corr_id, kv=kv)
        # Persist to JSONL file for quick diagnostics
        try:
            out_dir = "/opt/feature-factory/artifacts/ui"
            os.makedirs(out_dir, exist_ok=True)
            out_fp = os.path.join(out_dir, "client_logs.jsonl")
            rec = {
                "ts": ts,
                "level": payload.level,
                "message": payload.message,
                "stack": payload.stack,
                "url": payload.url,
                "user_agent": payload.user_agent,
                "ui_version": payload.ui_version,
                "extra": payload.extra,
                "corr_id": corr_id,
            }
            with open(out_fp, 'a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as fe:
            log.warning("ui_client_log_persist_failed", env=get_env(), component="ui", agent_role="UI", run_id=corr_id, correlation_id=corr_id, kv={"err": str(fe)})

        return {"status": "ok", "ts": ts, "corr_id": corr_id}
    except Exception as e:
        log.error("ui_client_log_ingest_failed", env=get_env(), component="ui", agent_role="UI", run_id=corr_id, task_id=str(uuid.uuid4()), correlation_id=corr_id, kv={"err": str(e)})
        raise HTTPException(status_code=500, detail="failed")


@router.post("/client")
async def ingest_client_log_post(payload: ClientLogPayload, request: Request):
    return await _ingest(payload, request)


@router.get("/client")
async def ingest_client_log_get(request: Request, level: str = 'error', message: str = '', stack: str | None = None, url: str | None = None, ui_version: str | None = None):
    payload = ClientLogPayload(level=level, message=message or 'client_log', stack=stack, url=url, ui_version=ui_version)
    return await _ingest(payload, request)


@router.get("/client/recent")
async def recent_client_logs(limit: int = 100):
    out_fp = "/opt/feature-factory/artifacts/ui/client_logs.jsonl"
    try:
        if not os.path.exists(out_fp):
            return {"items": [], "total": 0}
        # naive tail
        with open(out_fp, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-limit:]
        items = []
        for ln in lines:
            try:
                items.append(json.loads(ln))
            except Exception:
                continue
        return {"items": items, "total": len(items)}
    except Exception as e:
        log.error("ui_client_log_recent_failed", env=get_env(), component="ui", agent_role="UI", run_id=generate_correlation_id(), correlation_id=generate_correlation_id(), kv={"err": str(e)})
        raise HTTPException(status_code=500, detail="failed to read recent logs")

# Aliases without /logs prefix to avoid conflicts with other routers
@router2.post("/client-logs")
async def ingest_client_log_post_alt(payload: ClientLogPayload, request: Request):
    return await _ingest(payload, request)

@router2.get("/client-logs")
async def ingest_client_log_get_alt(request: Request, level: str = 'error', message: str = '', stack: str | None = None, url: str | None = None, ui_version: str | None = None):
    payload = ClientLogPayload(level=level, message=message or 'client_log', stack=stack, url=url, ui_version=ui_version)
    return await _ingest(payload, request)

@router2.get("/client-logs/recent")
async def recent_client_logs_alt(limit: int = 100):
    return await recent_client_logs(limit)
