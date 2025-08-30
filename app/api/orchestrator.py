#!/usr/bin/env python3
"""
API оркестратора для интеграции UI/скриптов.
"""

from fastapi import APIRouter
from app.api.orchestrator_v2 import router as orchestrator_v2_router

# Создаем роутер для оркестратора
router = APIRouter(prefix="/api/v1/orchestrator")

# Включаем роуты из новой реализации
router.include_router(orchestrator_v2_router)