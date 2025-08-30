#!/usr/bin/env python3
"""
Pydantic схемы для API maintainer, соответствующие спецификации API-Maintainer-001.md.
"""

from pydantic import BaseModel
from typing import Optional, List, Any, Dict, Union


# Схемы запросов
class MaintainerIntentRequest(BaseModel):
    """Схема запроса на генерацию intent из естественного языка."""
    nl_text: str


class MaintainerPlanRequest(BaseModel):
    """Схема запроса на генерацию плана из intent."""
    intent_json: Dict[str, Any]


# Вспомогательные схемы
class TaskDSL(BaseModel):
    """Схема задачи в DSL."""
    id: str
    name: str
    kind: str
    role: str
    preconditions: List[str]
    postconditions: List[str]
    idempotency_key: str
    retry: Dict[str, Any]
    deadline: str
    models: List[str]
    outputs: List[str]
    dod: List[str]
    severity: str


# Схемы ответов
class MaintainerIntentResponse(BaseModel):
    """Схема ответа на генерацию intent."""
    nl_text: str
    intent_json: Dict[str, Any]
    issues: List[str]
    suggestions: List[str]


class MaintainerPlanResponse(BaseModel):
    """Схема ответа на генерацию плана."""
    intent_json: Dict[str, Any]
    dag: List[TaskDSL]
    package_contract: Dict[str, Any]


# Схемы ошибок
class ErrorResponse(BaseModel):
    """Схема ответа об ошибке."""
    error: str
    detail: Optional[str] = None