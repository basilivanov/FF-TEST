#!/usr/bin/env python3
from __future__ import annotations

import uuid

from fastapi import APIRouter, Request, Response

from app.logging_helpers import log, get_env, generate_correlation_id
from app.metrics.registry import render_prometheus_text

router = APIRouter()


def _log(event: str, correlation_id: str, task_id: str, **kv) -> None:
    log.info(
        event=event,
        env=get_env(),
        component="metrics",
        agent_role="Ops",
        run_id=correlation_id,
        task_id=task_id,
        correlation_id=correlation_id,
        kv=kv,
    )


@router.get("/metrics")
def metrics(request: Request) -> Response:
    correlation_id = request.headers.get("x-correlation-id", generate_correlation_id())
    task_id = str(uuid.uuid4())

    text = render_prometheus_text()
    _log("metrics_served", correlation_id, task_id, payload_bytes=len(text.encode("utf-8")))

    return Response(content=text, media_type="text/plain; version=0.0.4; charset=utf-8")

