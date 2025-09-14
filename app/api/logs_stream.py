#!/usr/bin/env python3
"""
SSE под контракт /api/v1/logs/stream — события логов для UI/CI.
"""

import asyncio
import json
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.logging_helpers import log, get_env, generate_correlation_id

router = APIRouter(prefix="/api/v1/logs")


async def _gen(request: Request):
    connection_id = str(uuid.uuid4())
    log.info(event="sse_logs_stream_open", env=get_env(), component="sse", correlation_id=connection_id)
    try:
        # начальное событие
        yield f"event: open\ndata: {json.dumps({'connection_id': connection_id})}\n\n"
        i = 0
        while True:
            if await request.is_disconnected():
                break
            i += 1
            payload = {"seq": i, "queue_depth": 0, "last_tick_ms": 0}
            yield f"event: runner_tick\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(1)
    finally:
        log.info(event="sse_logs_stream_close", env=get_env(), component="sse", correlation_id=connection_id)


@router.get("/stream")
async def logs_stream(request: Request):
    return StreamingResponse(_gen(request), media_type="text/event-stream")

