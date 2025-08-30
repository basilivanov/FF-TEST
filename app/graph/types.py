#!/usr/bin/env python3
"""
Типы контекста узлов для LangGraph.
"""

from dataclasses import dataclass
from typing import Optional
import uuid

@dataclass
class RunCtx:
    """Контекст выполнения узла графа."""
    run_id: str
    feature_id: str
    task_id: str
    correlation_id: str
    env: str
    
    def __post_init__(self):
        """Проверка корректности данных после инициализации."""
        if not self.run_id:
            raise ValueError("run_id cannot be empty")
        if not self.feature_id:
            raise ValueError("feature_id cannot be empty")
        if not self.task_id:
            raise ValueError("task_id cannot be empty")
        if not self.correlation_id:
            raise ValueError("correlation_id cannot be empty")
        if not self.env:
            raise ValueError("env cannot be empty")