#!/usr/bin/env python3
"""
Admin endpoints to manage logging levels at runtime.

Security: HTTP Basic (ADMIN_USERNAME/ADMIN_PASSWORD)
Scope: TEST/PROD (use TTL overrides carefully in PROD)
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db.session import get_db
from sqlalchemy.orm import Session

from app.logging.config import apply_runtime_levels
from app.logging_helpers import log, get_env, generate_correlation_id


router = APIRouter(prefix="/api/v1/admin/logging", tags=["AdminLogging"])
security = HTTPBasic()

AUTH_USERNAME = os.getenv("ADMIN_USERNAME", "ops")
AUTH_PASSWORD = os.getenv("ADMIN_PASSWORD", "ops123")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == AUTH_USERNAME and credentials.password == AUTH_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


class SetLevelRequest(BaseModel):
    global_level: Optional[str] = Field(None, description="Global level (DEBUG|INFO|WARN|ERROR)")
    modules: Optional[Dict[str, str]] = Field(None, description="Mapping: module -> level")
    ttl_sec: Optional[int] = Field(900, description="Time-to-live for overrides, seconds")


class OverrideItem(BaseModel):
    id: int
    module: Optional[str]
    level: str
    expires_at: Optional[str]
    created_at: str


class StateResponse(BaseModel):
    overrides: List[OverrideItem]


@router.post("/set-level")
def set_level(payload: SetLevelRequest, username: str = Depends(verify_credentials), db: Session = Depends(get_db)) -> Dict[str, Any]:
    corr = generate_correlation_id()
    ttl = payload.ttl_sec or 900
    expires_at = _now_utc() + timedelta(seconds=max(1, ttl))

    # Apply immediately in-process
    apply_runtime_levels(payload.global_level, payload.modules)

    # Persist overrides
    # Schema: logging_config(id INTEGER PK, module TEXT NULL, level TEXT NOT NULL, expires_at DATETIME NULL, created_at DATETIME DEFAULT now)
    try:
        if payload.global_level:
            db.execute(
                text("INSERT INTO logging_config(module, level, expires_at, created_at) VALUES (NULL, :level, :expires, datetime('now'))"),
                {"level": payload.global_level.upper(), "expires": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")}
            )
        if payload.modules:
            for mod, lvl in payload.modules.items():
                db.execute(
                    text("INSERT INTO logging_config(module, level, expires_at, created_at) VALUES (:module, :level, :expires, datetime('now'))"),
                    {"module": mod, "level": lvl.upper(), "expires": expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")}
                )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to persist logging overrides: {e}")

    log.info(
        event="logging_overrides_set",
        env=get_env(),
        component="admin_logging",
        agent_role="System",
        correlation_id=corr,
        kv={"global": payload.global_level, "modules": payload.modules, "ttl_sec": ttl}
    )

    return {"status": "ok"}


def _prune_expired(db: Session) -> None:
    try:
        # Remove expired rows and do not apply them
        db.execute(text("DELETE FROM logging_config WHERE expires_at IS NOT NULL AND datetime(expires_at) < datetime('now')"))
        db.commit()
    except Exception:
        db.rollback()


@router.get("/state", response_model=StateResponse)
def get_state(username: str = Depends(verify_credentials), db: Session = Depends(get_db)) -> StateResponse:
    _prune_expired(db)
    rows = db.execute(text("SELECT id, module, level, expires_at, created_at FROM logging_config ORDER BY id DESC LIMIT 200"))
    items: List[OverrideItem] = []
    for r in rows.fetchall():
        items.append(OverrideItem(
            id=r[0],
            module=r[1],
            level=r[2],
            expires_at=(r[3] or ""),
            created_at=(r[4] or ""),
        ))
    return StateResponse(overrides=items)

