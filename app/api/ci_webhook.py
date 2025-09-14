#!/usr/bin/env python3
"""
GitHub Webhook endpoint: /api/v1/ci/webhook (HMAC SHA-256)
Обрабатываем как минимум событие check_suite: completed, conclusion=success.
На успех — создаём MERGE_PR задачу для соответствующей фичи.
"""

import hmac
import hashlib
import json
import os
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text
from app.db.session import get_db
from app.logging_helpers import log, get_env

router = APIRouter(prefix="/api/v1/ci")


def _verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    try:
        return hmac.compare_digest(expected, signature_header)
    except Exception:
        return False


@router.post("/webhook")
async def github_webhook(request: Request):
    # Read raw body for HMAC check
    body = await request.body()
    event = request.headers.get("X-GitHub-Event")
    sig = request.headers.get("X-Hub-Signature-256")
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    if not _verify_signature(secret, body, sig):
        log.warning("ci_webhook_signature_mismatch")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle check_suite: completed/success
    if event == "check_suite":
        action = payload.get("action")
        cs = payload.get("check_suite", {})
        conclusion = cs.get("conclusion")
        head_sha = cs.get("head_sha")
        prs = cs.get("pull_requests") or []
        if action == "completed" and conclusion == "success" and prs:
            pr_number = prs[0].get("number")
            # map PR to feature and create MERGE_PR task if not exists
            db_gen = get_db()
            db = next(db_gen)
            try:
                # Find feature by PR number in features.pr_url
                res = db.execute(text("SELECT id FROM features WHERE pr_url LIKE :p1 OR pr_url LIKE :p2"),
                                 {"p1": f"%/pull/{pr_number}%", "p2": f"%/pull/{pr_number}"})
                row = res.fetchone()
                if row:
                    feature_id = row[0]
                    # Check existing MERGE_PR task
                    cnt = db.execute(text("SELECT COUNT(*) FROM tasks WHERE feature_id=:f AND role='MERGE_PR' AND status IN ('NEW','RUNNING')"),
                                     {"f": feature_id}).fetchone()[0]
                    if cnt == 0:
                        db.execute(text("INSERT INTO tasks (feature_id, role, status, attempts, payload) VALUES (:f, 'MERGE_PR', 'NEW', 0, :sha)"),
                                   {"f": feature_id, "sha": head_sha or ""})
                        db.commit()
                        log.info("ci_webhook_merge_pr_created", feature_id=feature_id, pr_number=pr_number)
                else:
                    log.warning("ci_webhook_feature_not_found", pr_number=pr_number)
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass
    else:
        # For other events we simply acknowledge for now
        pass

    return {"status": "ok"}

