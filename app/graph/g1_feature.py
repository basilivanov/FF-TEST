#!/usr/bin/env python3
"""
Граф G1 для обработки фич.
"""

import asyncio
import uuid
import structlog
from langgraph.graph import StateGraph, END
from typing import Dict, Any, Optional, List

from app.graph.base import get_graph_manager, start_run, resume_run
from app.graph.types import RunCtx
from app.graph.nodes.dev_code import dev_code_node
from app.graph.nodes.gate import gate_node
from app.graph.nodes.qa import qa_node
from app.graph.nodes.scribe import scribe_node
from app.graph.nodes.apply import apply_node
from app.graph.nodes.watchdog import watchdog_check_node # Импорт Watchdog

# Настройка логгера
logger = structlog.get_logger()

# Определяем состояние графа
class GraphState(dict):
    """Состояние графа."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем обязательные поля состояния
        self.setdefault("run_ctx", None)
        self.setdefault("status", "initialized")
        self.setdefault("result", None)
        self.setdefault("error", None)
        # Поля для Watchdog
        self.setdefault("watchdog_failures", [])
        self.setdefault("escalation_context", "")
        self.setdefault("watchdog_decision", "CONTINUE")
        # Контекстный пакет (Markdown) от ContextPackager
        self.setdefault("context_pack", None)

# Функция решения для Watchdog
def decide_after_watchdog(state: GraphState) -> str:
    """Решает, куда идти после проверки Watchdog."""
    if state.get("watchdog_decision") == "ESCALATE_L1":
        return "dev"  # Возвращаемся к dev для повторной попытки с контекстом
    return "gate" # Продолжаем нормальный поток

# Создаем граф
def create_g1_graph() -> StateGraph:
    """
    Создает граф G1 для обработки фич.
    
    Returns:
        StateGraph: Граф G1
    """
    # Создаем граф
    workflow = StateGraph(GraphState)
    
    # Добавляем узлы
    workflow.add_node("dev", dev_code_node)
    workflow.add_node("watchdog_check", watchdog_check_node) # Узел Watchdog
    workflow.add_node("gate", gate_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("scribe", scribe_node)
    workflow.add_node("apply", apply_node)
    
    # Устанавливаем начальный узел
    workflow.set_entry_point("dev")

    # Добавляем ребра с учетом Watchdog
    workflow.add_edge("dev", "watchdog_check")
    workflow.add_conditional_edges(
        "watchdog_check",
        decide_after_watchdog,
        {
            "dev": "dev",
            "gate": "gate"
        }
    )
    
    # Остальные ребра
    workflow.add_edge("gate", "qa")
    workflow.add_edge("qa", "scribe")
    workflow.add_edge("scribe", "apply")
    workflow.add_edge("apply", END)
    
    return workflow

# Глобальный экземпляр графа
g1_graph = create_g1_graph()

def get_g1_graph() -> StateGraph:
    """
    Получает глобальный экземпляр графа G1.
    
    Returns:
        StateGraph: Глобальный экземпляр графа G1
    """
    return g1_graph
