#!/usr/bin/env python3
"""
Модуль для защиты базы данных от использования неправильных путей.
"""

import os
import structlog
from typing import Dict, Any

# Настройка логгера
logger = structlog.get_logger()

# Ожидаемые пути к БД для разных окружений
EXPECTED_DB_PATHS = {
    "TEST": "sqlite:////opt/feature-factory/data/test.db",
    "PROD": "sqlite:////opt/feature-factory/data/prod.db"
}

class FAILED_NEEDS_ATTENTION(Exception):
    """Исключение, выбрасываемое при несовпадении пути к БД."""
    pass

class DbPathMismatch(Exception):
    """Исключение, выбрасываемое при несовпадении пути к БД."""
    pass

def get_env() -> str:
    """Получает текущее окружение."""
    return os.getenv("ENV", "TEST")

def get_db_connection_string() -> str:
    """Получает строку подключения к БД."""
    return os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")

def guard_db_path(current_db_url: str) -> None:
    """
    Проверяет, соответствует ли текущий путь к БД ожидаемому для текущего окружения.
    
    Args:
        current_db_url (str): Текущий URL базы данных
        
    Raises:
        FAILED_NEEDS_ATTENTION: Если путь к БД не совпадает с ожидаемым
    """
    try:
        # Получаем текущее окружение
        env = get_env()
        
        # Получаем ожидаемый путь для текущего окружения
        expected_db_url = EXPECTED_DB_PATHS.get(env)
        
        # Если нет ожидаемого пути для окружения, это ошибка конфигурации
        if expected_db_url is None:
            logger.error(
                "db_guard_error",
                component="db",
                err_type="DbPathMismatch",
                env=env,
                current_db_url=current_db_url,
                expected_db_url=None,
                error="No expected DB URL for environment"
            )
            raise FAILED_NEEDS_ATTENTION(f"No expected DB URL for environment {env}")
        
        # Проверяем соответствие путей
        if current_db_url != expected_db_url:
            logger.error(
                "db_guard_error",
                component="db",
                err_type="DbPathMismatch",
                env=env,
                current_db_url=current_db_url,
                expected_db_url=expected_db_url
            )
            raise FAILED_NEEDS_ATTENTION(
                f"DB path mismatch for {env} environment. "
                f"Expected: {expected_db_url}, got: {current_db_url}"
            )
        
        # Если пути совпадают, логируем успешную проверку
        logger.info(
            "db_guard_success",
            component="db",
            env=env,
            current_db_url=current_db_url
        )
        
    except FAILED_NEEDS_ATTENTION:
        # Переподнимем исключение FAILED_NEEDS_ATTENTION
        raise
    except Exception as e:
        # Логируем любые другие ошибки
        logger.error(
            "db_guard_unexpected_error",
            component="db",
            err_type=type(e).__name__,
            error=str(e),
            current_db_url=current_db_url
        )
        raise FAILED_NEEDS_ATTENTION(f"Unexpected error during DB guard check: {e}") from e