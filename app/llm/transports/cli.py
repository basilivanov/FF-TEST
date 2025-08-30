#!/usr/bin/env python3
"""
Модуль для низкоуровневого запуска CLI команд для взаимодействия с LLM.
"""

import subprocess
import os
from typing import List, Dict, Tuple
import structlog

# Настройка логгера
logger = structlog.get_logger()

class CliTransportError(Exception):
    """Базовый класс для ошибок транспорта CLI."""
    pass

class CliExecError(CliTransportError):
    """Ошибка выполнения CLI команды."""
    pass

class CliTimeoutError(CliTransportError):
    """Таймаут при выполнении CLI команды."""
    pass

def run_cli(cmd: List[str], env: Dict[str, str], timeout_s: int, input_data: str | None = None) -> Tuple[int, str, str]:
    """
    Запускает CLI команду и возвращает результат.
    
    Args:
        cmd: Список аргументов команды.
        env: Словарь переменных окружения.
        timeout_s: Таймаут выполнения в секундах.
        
    Returns:
        Tuple[int, str, str]: (код возврата, stdout, stderr)
        
    Raises:
        CliExecError: При ошибке выполнения команды (rc != 0).
        CliTimeoutError: При таймауте выполнения.
    """
    # Объединяем переданное окружение с текущим
    full_env = {**os.environ, **env}
    
    logger.info(
        "llm_call_start",
        command=" ".join(cmd),  # Full command
        env_keys=list(env.keys()),
        timeout=timeout_s,
        input_data_preview=(input_data[:200] if isinstance(input_data, str) else "(empty)")
    )

    try:
        # Запуск команды с таймаутом, без shell=True
        result = subprocess.run(
            cmd,
            env=full_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
            check=False  # Не выбрасывать исключение при ненулевом коде возврата
            ,
            input=input_data
        )
        
        # llm_call_end logging
        logger.info(
            "llm_call_end",
            command=" ".join(cmd), # Full command
            returncode=result.returncode,
            stderr=result.stderr.strip(), # Stderr without tokens
            stdout_len=len(result.stdout),
            timeout=timeout_s
        )
        
        # Если код возврата не 0, классифицируем как RETRYABLE_ERROR
        if result.returncode != 0:
            logger.error(
                "cli_exec_error",
                component="llm",
                err_type="CliExecError",
                cmd=cmd,
                returncode=result.returncode,
                stderr=result.stderr,
                stdout_preview=result.stdout[:300]
            )
            raise CliExecError(f"CLI command failed with return code {result.returncode}: {result.stderr}")
        
        return (result.returncode, result.stdout, result.stderr)
    
    except subprocess.TimeoutExpired as e:
        logger.error(
            "cli_exec_timeout",
            component="llm",
            err_type="CliTimeout",
            cmd=cmd,
            timeout=timeout_s
        )
        raise CliTimeoutError(f"CLI command timed out after {timeout_s} seconds") from e
    
    except CliTransportError:  # Не перехватываем уже обработанные ошибки транспорта
        raise
    except Exception as e:
        logger.error(
            "cli_exec_unexpected_error",
            component="llm",
            err_type=type(e).__name__,
            cmd=cmd,
            error=str(e)
        )
        raise CliTransportError(f"Unexpected error during CLI execution: {e}") from e
