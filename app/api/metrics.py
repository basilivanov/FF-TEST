#!/usr/bin/env python3
from __future__ import annotations

from fastapi import APIRouter, Response
from app.metrics.registry import render_prometheus_text

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    text = render_prometheus_text()
    return Response(content=text, media_type="text/plain; version=0.0.4; charset=utf-8")

