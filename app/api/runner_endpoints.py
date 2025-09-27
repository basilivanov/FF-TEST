#!/usr/bin/env python3
"""
Runner endpoints: ручной однократный тик обработчика бэклога.
Соответствует контракту: POST /api/v1/runner/run-once
"""

from fastapi import APIRouter, Request, HTTPException, status
import time
import uuid
from app.logging_helpers import log, get_env, generate_correlation_id

router = APIRouter(prefix="/api/v1/runner")


@router.post("/run-once")
async def run_once(request: Request):
    start_time = time.time()
    corr_id = request.headers.get("x-correlation-id") or generate_correlation_id()
    log.info(
        event="api_call_start",
        env=get_env(),
        component="runner_api",
        agent_role="System",
        run_id=corr_id,
        task_id=str(uuid.uuid4()),
        correlation_id=corr_id,
        kv={"endpoint": "POST /runner/run-once"}
    )
    try:
        from app.orchestrator.loop import get_orchestrator_loop
        loop = get_orchestrator_loop()
        await loop._process_backlog()
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            event="api_call_end",
            env=get_env(),
            component="runner_api",
            agent_role="System",
            run_id=corr_id,
            task_id=str(uuid.uuid4()),
            correlation_id=corr_id,
            kv={"status": 200, "duration_ms": round(duration_ms, 2)}
        )
        return {"status": "ok", "duration_ms": round(duration_ms, 2)}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log.error(
            event="api_call_end",
            env=get_env(),
            component="runner_api",
            agent_role="System",
            run_id=corr_id,
            task_id=str(uuid.uuid4()),
            correlation_id=corr_id,
            kv={"status": 500, "duration_ms": round(duration_ms, 2), "err_type": type(e).__name__, "err_msg": str(e)},
            stack=True
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

