#!/usr/bin/env python3
"""
MVP API для безопасного приёма и хранения секретов.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.db.session import get_db
from app.utils.secret_store import encrypt_value, mask_value

router = APIRouter(prefix="/api/v1/secrets")


def _ensure_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                value_enc TEXT NOT NULL,
                scope TEXT NOT NULL,
                owner TEXT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    db.commit()


class SecretUpsertRequest(BaseModel):
    key: str = Field(..., min_length=3, max_length=128)
    value: str = Field(..., min_length=1, max_length=4096)
    scope: str = Field("test", pattern=r"^(test|prod)$")
    owner: str | None = None


class SecretMaskedResponse(BaseModel):
    key: str
    masked: str
    scope: str
    updated_at: str


@router.post("/upsert", response_model=SecretMaskedResponse)
async def upsert_secret(req: Request, payload: SecretUpsertRequest, db: Session = Depends(get_db)):
    _ensure_table(db)
    now = datetime.utcnow().isoformat(timespec="seconds")
    try:
        value_enc = encrypt_value(payload.value)
        db.execute(
            text(
                """
                INSERT INTO secrets(key, value_enc, scope, owner, created_at, updated_at)
                VALUES (:k, :v, :s, :o, :ts, :ts)
                ON CONFLICT(key) DO UPDATE SET
                    value_enc = excluded.value_enc,
                    scope = excluded.scope,
                    owner = COALESCE(excluded.owner, secrets.owner),
                    updated_at = excluded.updated_at
                """
            ),
            {"k": payload.key, "v": value_enc, "s": payload.scope, "o": payload.owner, "ts": now},
        )
        db.commit()
        return SecretMaskedResponse(key=payload.key, masked=mask_value(payload.value), scope=payload.scope, updated_at=now)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store secret: {e}")


@router.get("/{key}", response_model=SecretMaskedResponse)
async def get_secret_masked(key: str, db: Session = Depends(get_db)):
    _ensure_table(db)
    row = db.execute(text("SELECT value_enc, scope, updated_at FROM secrets WHERE key = :k"), {"k": key}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Secret not found")
    # Возвращаем только маску
    masked = "****"
    scope = row[1]
    updated_at = row[2] or ""
    return SecretMaskedResponse(key=key, masked=masked, scope=scope, updated_at=updated_at)

