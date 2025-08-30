#!/usr/bin/env python3
"""
LLM endpoints: health for CLI providers.
"""

from __future__ import annotations
from fastapi import APIRouter
from app.llm.cli_path_guard import get_health_check_result

router = APIRouter(prefix="/api/v1/llm")


@router.get("/health")
def llm_health():
    return get_health_check_result()

