#!/usr/bin/env python3
"""
Модуль с декораторами для логирования различных операций в приложении.

Соответствует стандарту Logging-001.md.
"""

#!/usr/bin/env python3
"""
Модуль с декораторами для логирования различных операций в приложении.

Соответствует стандарту Logging-001.md.
"""

import os
import time
import uuid
import functools
import traceback
from typing import Any, Callable, Dict, Optional
import structlog
from loguru import logger


# Настройка structlog для JSON логов
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# Глобальный логгер
log = structlog.get_logger()


def get_env() -> str:
    """Получает текущее окружение (test или prod)."""
    return os.getenv("ENV", "test")


def generate_correlation_id() -> str:
    """Генерирует уникальный correlation_id."""
    return str(uuid.uuid4())


def log_job(job_name: str):
    """
    Декоратор для логирования начала и завершения выполнения задачи.
    
    Args:
        job_name (str): Название задачи
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем correlation_id если его нет
            correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
            task_id = kwargs.get('task_id') or str(uuid.uuid4())
            
            # Логируем начало задачи
            log.info(
                event="job_started",
                env=get_env(),
                component="job",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "job_name": job_name
                }
            )
            
            start_time = time.time()
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем успешное завершение задачи
                duration_ms = (time.time() - start_time) * 1000
                log.info(
                    event="job_finished",
                    env=get_env(),
                    component="job",
                    agent_role="Dev",
                    run_id=correlation_id,
                    task_id=task_id,
                    correlation_id=correlation_id,
                    kv={
                        "job_name": job_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success"
                    }
                )
                
                return result
            except Exception as e:
                # Логируем ошибку
                duration_ms = (time.time() - start_time) * 1000
                log.error(
                    event="job_finished",
                    env=get_env(),
                    component="job",
                    agent_role="Dev",
                    run_id=correlation_id,
                    task_id=task_id,
                    correlation_id=correlation_id,
                    kv={
                        "job_name": job_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "err_type": type(e).__name__,
                        "err_msg": str(e)
                    },
                    stack=True
                )
                raise
        return wrapper
    return decorator


def log_http(func: Callable) -> Callable:
    """
    Декоратор для логирования HTTP вызовов.
    
    Args:
        func (Callable): Функция для декорирования
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем параметры запроса
        method = kwargs.get('method', 'GET')
        url = kwargs.get('url', '')
        correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
        task_id = kwargs.get('task_id') or str(uuid.uuid4())
        
        # Разбираем URL для логирования
        url_host = ''
        url_path = ''
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url_host = parsed.netloc
            url_path = parsed.path
        
        # Логируем начало HTTP вызова
        log.info(
            event="api_call_start",
            env=get_env(),
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "method": method,
                "url_host": url_host,
                "url_path": url_path
            }
        )
        
        start_time = time.time()
        try:
            # Выполняем HTTP вызов
            result = func(*args, **kwargs)
            
            # Извлекаем информацию о ответе
            status = getattr(result, 'status_code', 200) if result else 200
            resp_bytes = len(getattr(result, 'content', b'')) if result else 0
            
            # Логируем завершение HTTP вызова
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                event="api_call_end",
                env=get_env(),
                component="api",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "method": method,
                    "url_host": url_host,
                    "url_path": url_path,
                    "status": status,
                    "duration_ms": round(duration_ms, 2),
                    "resp_bytes": resp_bytes
                }
            )
            
            return result
        except Exception as e:
            # Логируем ошибку HTTP вызова
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                event="api_call_end",
                env=get_env(),
                component="api",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "method": method,
                    "url_host": url_host,
                    "url_path": url_path,
                    "status": "error",
                    "duration_ms": round(duration_ms, 2),
                    "err_type": type(e).__name__,
                    "err_msg": str(e)
                },
                stack=True
            )
            raise
    return wrapper


def log_db(func: Callable) -> Callable:
    """
    Декоратор для логирования операций с базой данных.
    
    Args:
        func (Callable): Функция для декорирования
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем параметры операции
        table = kwargs.get('table', 'unknown')
        op = kwargs.get('op', 'unknown')
        correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
        task_id = kwargs.get('task_id') or str(uuid.uuid4())
        
        # Логируем начало операции с БД
        log.info(
            event="db_upsert",
            env=get_env(),
            component="db",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "table": table,
                "op": op
            }
        )
        
        start_time = time.time()
        try:
            # Выполняем операцию с БД
            result = func(*args, **kwargs)
            
            # Извлекаем информацию о результатах
            rows = kwargs.get('rows', 0)
            
            # Логируем завершение операции с БД
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                event="db_upsert",
                env=get_env(),
                component="db",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "table": table,
                    "op": op,
                    "rows": rows,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return result
        except Exception as e:
            # Логируем ошибку операции с БД
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                event="db_upsert",
                env=get_env(),
                component="db",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "table": table,
                    "op": op,
                    "duration_ms": round(duration_ms, 2),
                    "err_type": type(e).__name__,
                    "err_msg": str(e)
                },
                stack=True
            )
            raise
    return wrapper


def llm_log_context(provider: str, model: str, prompt_hash: str, input_tokens: int = 0, 
                   output_tokens: int = 0, latency_ms: float = 0.0, cache_hit: bool = False,
                   budget_remaining: Optional[float] = None) -> Dict[str, Any]:
    """
    Создает контекст логирования для LLM вызовов.
    
    Args:
        provider (str): Провайдер LLM
        model (str): Модель LLM
        prompt_hash (str): Хэш промпта
        input_tokens (int): Количество входных токенов
        output_tokens (int): Количество выходных токенов
        latency_ms (float): Задержка в миллисекундах
        cache_hit (bool): Был ли кэш-хит
        budget_remaining (Optional[float]): Оставшийся бюджет
        
    Returns:
        Dict[str, Any]: Контекст для логирования
    """
    kv = {
        "provider": provider,
        "model": model,
        "prompt_hash": prompt_hash,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cache_hit": cache_hit
    }
    
    if budget_remaining is not None:
        kv["budget_remaining"] = budget_remaining
    
    return kv

def log_llm_call(provider: str, model: str, prompt: str, response: str, 
                 agent_role: str, budget_remaining: Optional[float] = None):
    """
    Логирует LLM вызов с учетом токенов.
    
    Args:
        provider (str): Провайдер LLM
        model (str): Название модели
        prompt (str): Промпт
        response (str): Ответ
        agent_role (str): Роль агента
        budget_remaining (Optional[float]): Оставшийся бюджет
    """
    try:
        # Импортируем счетчик токенов
        from app.llm.token_accountant import get_token_accountant
        token_accountant = get_token_accountant()
        
        # Подсчитываем токены и логируем вызов
        token_accountant.log_llm_call(provider, model, prompt, response, agent_role, budget_remaining)
    except Exception as e:
        log.error("llm_logging_error", error=str(e))


def get_env() -> str:
    """Получает текущее окружение (test или prod)."""
    return os.getenv("ENV", "test")


def generate_correlation_id() -> str:
    """Генерирует уникальный correlation_id."""
    return str(uuid.uuid4())


def log_job(job_name: str):
    """
    Декоратор для логирования начала и завершения выполнения задачи.
    
    Args:
        job_name (str): Название задачи
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем correlation_id если его нет
            correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
            task_id = kwargs.get('task_id') or str(uuid.uuid4())
            
            # Логируем начало задачи
            log.info(
                event="job_started",
                env=get_env(),
                component="job",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "job_name": job_name
                }
            )
            
            start_time = time.time()
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем успешное завершение задачи
                duration_ms = (time.time() - start_time) * 1000
                log.info(
                    event="job_finished",
                    env=get_env(),
                    component="job",
                    agent_role="Dev",
                    run_id=correlation_id,
                    task_id=task_id,
                    correlation_id=correlation_id,
                    kv={
                        "job_name": job_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success"
                    }
                )
                
                return result
            except Exception as e:
                # Логируем ошибку
                duration_ms = (time.time() - start_time) * 1000
                log.error(
                    event="job_finished",
                    env=get_env(),
                    component="job",
                    agent_role="Dev",
                    run_id=correlation_id,
                    task_id=task_id,
                    correlation_id=correlation_id,
                    kv={
                        "job_name": job_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "err_type": type(e).__name__,
                        "err_msg": str(e)
                    },
                    stack=True
                )
                raise
        return wrapper
    return decorator


def log_http(func: Callable) -> Callable:
    """
    Декоратор для логирования HTTP вызовов.
    
    Args:
        func (Callable): Функция для декорирования
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем параметры запроса
        method = kwargs.get('method', 'GET')
        url = kwargs.get('url', '')
        correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
        task_id = kwargs.get('task_id') or str(uuid.uuid4())
        
        # Разбираем URL для логирования
        url_host = ''
        url_path = ''
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url_host = parsed.netloc
            url_path = parsed.path
        
        # Логируем начало HTTP вызова
        log.info(
            event="api_call_start",
            env=get_env(),
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "method": method,
                "url_host": url_host,
                "url_path": url_path
            }
        )
        
        start_time = time.time()
        try:
            # Выполняем HTTP вызов
            result = func(*args, **kwargs)
            
            # Извлекаем информацию о ответе
            status = getattr(result, 'status_code', 200) if result else 200
            resp_bytes = len(getattr(result, 'content', b'')) if result else 0
            
            # Логируем завершение HTTP вызова
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                event="api_call_end",
                env=get_env(),
                component="api",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "method": method,
                    "url_host": url_host,
                    "url_path": url_path,
                    "status": status,
                    "duration_ms": round(duration_ms, 2),
                    "resp_bytes": resp_bytes
                }
            )
            
            return result
        except Exception as e:
            # Логируем ошибку HTTP вызова
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                event="api_call_end",
                env=get_env(),
                component="api",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "method": method,
                    "url_host": url_host,
                    "url_path": url_path,
                    "status": "error",
                    "duration_ms": round(duration_ms, 2),
                    "err_type": type(e).__name__,
                    "err_msg": str(e)
                },
                stack=True
            )
            raise
    return wrapper


def log_db(func: Callable) -> Callable:
    """
    Декоратор для логирования операций с базой данных.
    
    Args:
        func (Callable): Функция для декорирования
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем параметры операции
        table = kwargs.get('table', 'unknown')
        op = kwargs.get('op', 'unknown')
        correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
        task_id = kwargs.get('task_id') or str(uuid.uuid4())
        
        # Логируем начало операции с БД
        log.info(
            event="db_upsert",
            env=get_env(),
            component="db",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "table": table,
                "op": op
            }
        )
        
        start_time = time.time()
        try:
            # Выполняем операцию с БД
            result = func(*args, **kwargs)
            
            # Извлекаем информацию о результатах
            rows = kwargs.get('rows', 0)
            
            # Логируем завершение операции с БД
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                event="db_upsert",
                env=get_env(),
                component="db",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "table": table,
                    "op": op,
                    "rows": rows,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return result
        except Exception as e:
            # Логируем ошибку операции с БД
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                event="db_upsert",
                env=get_env(),
                component="db",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "table": table,
                    "op": op,
                    "duration_ms": round(duration_ms, 2),
                    "err_type": type(e).__name__,
                    "err_msg": str(e)
                },
                stack=True
            )
            raise
    return wrapper


def llm_log_context(provider: str, model: str, prompt_hash: str, input_tokens: int = 0, 
                   output_tokens: int = 0, latency_ms: float = 0.0, cache_hit: bool = False,
                   budget_remaining: Optional[float] = None) -> Dict[str, Any]:
    """
    Создает контекст логирования для LLM вызовов.
    
    Args:
        provider (str): Провайдер LLM
        model (str): Модель LLM
        prompt_hash (str): Хэш промпта
        input_tokens (int): Количество входных токенов
        output_tokens (int): Количество выходных токенов
        latency_ms (float): Задержка в миллисекундах
        cache_hit (bool): Был ли кэш-хит
        budget_remaining (Optional[float]): Оставшийся бюджет
        
    Returns:
        Dict[str, Any]: Контекст для логирования
    """
    kv = {
        "provider": provider,
        "model": model,
        "prompt_hash": prompt_hash,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cache_hit": cache_hit
    }
    
    if budget_remaining is not None:
        kv["budget_remaining"] = budget_remaining
    
    return kv

def log_llm_call(provider: str, model: str, prompt: str, response: str, 
                 agent_role: str, budget_remaining: Optional[float] = None):
    """
    Логирует LLM вызов с учетом токенов.
    
    Args:
        provider (str): Провайдер LLM
        model (str): Название модели
        prompt (str): Промпт
        response (str): Ответ
        agent_role (str): Роль агента
        budget_remaining (Optional[float]): Оставшийся бюджет
    """
    try:
        # Импортируем счетчик токенов
        from app.llm.token_accountant import get_token_accountant
        token_accountant = get_token_accountant()
        
        # Подсчитываем токены и логируем вызов
        token_accountant.log_llm_call(provider, model, prompt, response, agent_role, budget_remaining)
    except Exception as e:
        log.error("llm_logging_error", error=str(e))

# Глобальный логгер
log = structlog.get_logger()


def get_env() -> str:
    """Получает текущее окружение (test или prod)."""
    return os.getenv("ENV", "test")


def generate_correlation_id() -> str:
    """Генерирует уникальный correlation_id."""
    return str(uuid.uuid4())


def log_job(job_name: str):
    """
    Декоратор для логирования начала и завершения выполнения задачи.
    
    Args:
        job_name (str): Название задачи
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем correlation_id если его нет
            correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
            task_id = kwargs.get('task_id') or str(uuid.uuid4())
            
            # Логируем начало задачи
            log.info(
                event="job_started",
                env=get_env(),
                component="job",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "job_name": job_name
                }
            )
            
            start_time = time.time()
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем успешное завершение задачи
                duration_ms = (time.time() - start_time) * 1000
                log.info(
                    event="job_finished",
                    env=get_env(),
                    component="job",
                    agent_role="Dev",
                    run_id=correlation_id,
                    task_id=task_id,
                    correlation_id=correlation_id,
                    kv={
                        "job_name": job_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success"
                    }
                )
                
                return result
            except Exception as e:
                # Логируем ошибку
                duration_ms = (time.time() - start_time) * 1000
                log.error(
                    event="job_finished",
                    env=get_env(),
                    component="job",
                    agent_role="Dev",
                    run_id=correlation_id,
                    task_id=task_id,
                    correlation_id=correlation_id,
                    kv={
                        "job_name": job_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "err_type": type(e).__name__,
                        "err_msg": str(e)
                    },
                    stack=True
                )
                raise
        return wrapper
    return decorator


def log_http(func: Callable) -> Callable:
    """
    Декоратор для логирования HTTP вызовов.
    
    Args:
        func (Callable): Функция для декорирования
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем параметры запроса
        method = kwargs.get('method', 'GET')
        url = kwargs.get('url', '')
        correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
        task_id = kwargs.get('task_id') or str(uuid.uuid4())
        
        # Разбираем URL для логирования
        url_host = ''
        url_path = ''
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url_host = parsed.netloc
            url_path = parsed.path
        
        # Логируем начало HTTP вызова
        log.info(
            event="api_call_start",
            env=get_env(),
            component="api",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "method": method,
                "url_host": url_host,
                "url_path": url_path
            }
        )
        
        start_time = time.time()
        try:
            # Выполняем HTTP вызов
            result = func(*args, **kwargs)
            
            # Извлекаем информацию о ответе
            status = getattr(result, 'status_code', 200) if result else 200
            resp_bytes = len(getattr(result, 'content', b'')) if result else 0
            
            # Логируем завершение HTTP вызова
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                event="api_call_end",
                env=get_env(),
                component="api",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "method": method,
                    "url_host": url_host,
                    "url_path": url_path,
                    "status": status,
                    "duration_ms": round(duration_ms, 2),
                    "resp_bytes": resp_bytes
                }
            )
            
            return result
        except Exception as e:
            # Логируем ошибку HTTP вызова
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                event="api_call_end",
                env=get_env(),
                component="api",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "method": method,
                    "url_host": url_host,
                    "url_path": url_path,
                    "status": "error",
                    "duration_ms": round(duration_ms, 2),
                    "err_type": type(e).__name__,
                    "err_msg": str(e)
                },
                stack=True
            )
            raise
    return wrapper


def log_db(func: Callable) -> Callable:
    """
    Декоратор для логирования операций с базой данных.
    
    Args:
        func (Callable): Функция для декорирования
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем параметры операции
        table = kwargs.get('table', 'unknown')
        op = kwargs.get('op', 'unknown')
        correlation_id = kwargs.get('correlation_id') or generate_correlation_id()
        task_id = kwargs.get('task_id') or str(uuid.uuid4())
        
        # Логируем начало операции с БД
        log.info(
            event="db_upsert",
            env=get_env(),
            component="db",
            agent_role="Dev",
            run_id=correlation_id,
            task_id=task_id,
            correlation_id=correlation_id,
            kv={
                "table": table,
                "op": op
            }
        )
        
        start_time = time.time()
        try:
            # Выполняем операцию с БД
            result = func(*args, **kwargs)
            
            # Извлекаем информацию о результатах
            rows = kwargs.get('rows', 0)
            
            # Логируем завершение операции с БД
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                event="db_upsert",
                env=get_env(),
                component="db",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "table": table,
                    "op": op,
                    "rows": rows,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return result
        except Exception as e:
            # Логируем ошибку операции с БД
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                event="db_upsert",
                env=get_env(),
                component="db",
                agent_role="Dev",
                run_id=correlation_id,
                task_id=task_id,
                correlation_id=correlation_id,
                kv={
                    "table": table,
                    "op": op,
                    "duration_ms": round(duration_ms, 2),
                    "err_type": type(e).__name__,
                    "err_msg": str(e)
                },
                stack=True
            )
            raise
    return wrapper


def llm_log_context(provider: str, model: str, prompt_hash: str, input_tokens: int = 0, 
                   output_tokens: int = 0, latency_ms: float = 0.0, cache_hit: bool = False,
                   budget_remaining: Optional[float] = None) -> Dict[str, Any]:
    """
    Создает контекст логирования для LLM вызовов.
    
    Args:
        provider (str): Провайдер LLM
        model (str): Модель LLM
        prompt_hash (str): Хэш промпта
        input_tokens (int): Количество входных токенов
        output_tokens (int): Количество выходных токенов
        latency_ms (float): Задержка в миллисекундах
        cache_hit (bool): Был ли кэш-хит
        budget_remaining (Optional[float]): Оставшийся бюджет
        
    Returns:
        Dict[str, Any]: Контекст для логирования
    """
    kv = {
        "provider": provider,
        "model": model,
        "prompt_hash": prompt_hash,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cache_hit": cache_hit
    }
    
    if budget_remaining is not None:
        kv["budget_remaining"] = budget_remaining
    
    return kv

def log_llm_call(provider: str, model: str, prompt: str, response: str, 
                 agent_role: str, budget_remaining: Optional[float] = None):
    """
    Логирует LLM вызов с учетом токенов.
    
    Args:
        provider (str): Провайдер LLM
        model (str): Название модели
        prompt (str): Промпт
        response (str): Ответ
        agent_role (str): Роль агента
        budget_remaining (Optional[float]): Оставшийся бюджет
    """
    try:
        # Импортируем счетчик токенов
        from app.llm.token_accountant import get_token_accountant
        token_accountant = get_token_accountant()
        
        # Подсчитываем токены и логируем вызов
        token_accountant.log_llm_call(provider, model, prompt, response, agent_role, budget_remaining)
    except Exception as e:
        log.error("llm_logging_error", error=str(e))