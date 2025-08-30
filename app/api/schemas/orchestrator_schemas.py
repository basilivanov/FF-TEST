#!/usr/bin/env python3
"""
Pydantic схемы для API оркестратора, соответствующие спецификации API-Orchestrator-001.md.
"""

from pydantic import BaseModel
from typing import Optional, List, Any, Dict, Union


# Схемы запросов
class FeatureCreateRequest(BaseModel):
    """Схема запроса на создание фичи."""
    title: str
    intent: Optional[Union[Dict[str, Any], None]] = None
    autostart: Optional[bool] = None
    strict: Optional[bool] = None
    strict_hard: Optional[bool] = None


# Схемы ответов
class FeatureCreatedResponse(BaseModel):
    """Схема ответа на создание фичи."""
    id: int
    status: str  # "NEW" | "PLANNED" | "RUNNING" | "DONE" | "FAILED"


class TaskPlanResponse(BaseModel):
    """Схема задачи в ответе на планирование."""
    id: int
    role: str
    status: str  # Всегда "NEW" согласно спецификации


class PlanResponse(BaseModel):
    """Схема ответа на планирование фичи."""
    feature_id: int
    tasks: List[TaskPlanResponse]
    package_contract: Dict[str, Any]


class RunResponse(BaseModel):
    """Схема ответа на запуск фичи."""
    run_id: str
    state: str  # "STARTED" | "RESUMED"


class GraphStatusResponse(BaseModel):
    """Схема ответа на запрос статуса графа."""
    run_id: str
    graph: str  # Всегда "G1" согласно спецификации
    status: str  # "RUNNING" | "DONE" | "FAILED"
    feature_status: str  # "NEW" | "RUNNING" | "DONE" | "FAILED"
    last_checkpoint: str
    env: str


class GraphRunListItem(BaseModel):
    """Схема элемента списка запусков для UI Dashboard."""
    run_id: str
    feature_id: int
    feature_title: str
    graph_name: Optional[str] = None
    thread_id: Optional[str] = None
    state_json: Optional[str] = None
    status: str
    last_checkpoint_at: str
    env: str


# Схемы ошибок
class ErrorResponse(BaseModel):
    """Схема ответа об ошибке."""
    error_code: str
    detail: str
