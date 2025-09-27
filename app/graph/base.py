#!/usr/bin/env python3
"""
Базовый модуль для работы с LangGraph и чекпоинтером.
"""

import os
import uuid
import structlog
from langgraph.checkpoint.memory import MemorySaver
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
except (ImportError, ModuleNotFoundError):
    SqliteSaver = None  # type: ignore
from app.logging_helpers import get_env

# Настройка логгера
logger = structlog.get_logger()

# Путь к файлу чекпоинтов
CHECKPOINTS_DB_PATH = "/opt/feature-factory/data/checkpoints.db"

class GraphManager:
    """Менеджер для работы с графом и чекпоинтером."""
    
    def __init__(self):
        """Инициализирует менеджер графа."""
        self.checkpointer = None
        self._initialize_checkpointer()
    
    def _initialize_checkpointer(self):
        """Инициализирует чекпоинтер SQLite."""
        try:
            # Создаем каталог для данных, если его нет
            data_dir = os.path.dirname(CHECKPOINTS_DB_PATH)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            
            # Инициализируем чекпоинтер
            if SqliteSaver is not None:
                self.checkpointer = SqliteSaver.from_conn_string(CHECKPOINTS_DB_PATH)
                logger.info(
                    "checkpointer_initialized",
                    component="graph",
                    db_path=CHECKPOINTS_DB_PATH
                )
            else:
                self.checkpointer = MemorySaver()
                logger.warning(
                    "checkpointer_fallback_memory",
                    component="graph",
                    reason="sqlite_backend_missing"
                )
        except Exception as e:
            logger.error(
                "checkpointer_init_failed",
                component="graph",
                err_type=type(e).__name__,
                error=str(e),
                db_path=CHECKPOINTS_DB_PATH
            )
            raise

# Глобальный экземпляр менеджера графа
graph_manager = GraphManager()

def get_graph_manager() -> GraphManager:
    """
    Получает глобальный экземпляр менеджера графа.
    
    Returns:
        GraphManager: Глобальный экземпляр менеджера графа
    """
    return graph_manager

def start_run(feature_id: str) -> str:
    """
    Начинает новый запуск графа.
    
    Args:
        feature_id (str): Идентификатор фичи
        
    Returns:
        str: Идентификатор запуска (run_id)
    """
    try:
        # Генерируем новый run_id
        run_id = str(uuid.uuid4())
        
        logger.info(
            event="run_started",
            env=get_env(),
            component="graph",
            agent_role="GraphManager",
            run_id=run_id,
            task_id=str(uuid.uuid4()),
            correlation_id=run_id,
            kv={
                "feature_id": feature_id,
                "graph_type": "G1"
            }
        )
        
        return run_id
    except Exception as e:
        logger.error(
            "run_start_failed",
            component="graph",
            err_type=type(e).__name__,
            error=str(e),
            feature_id=feature_id
        )
        raise

def resume_run(run_id: str) -> None:
    """
    Возобновляет прерванный запуск графа.
    
    Args:
        run_id (str): Идентификатор запуска
    """
    try:
        logger.info(
            "run_resumed",
            component="graph",
            run_id=run_id
        )
    except Exception as e:
        logger.error(
            "run_resume_failed",
            component="graph",
            err_type=type(e).__name__,
            error=str(e),
            run_id=run_id
        )
        raise