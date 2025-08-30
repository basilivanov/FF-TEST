import pytest
import uuid
from unittest.mock import patch, MagicMock
from app.logging_helpers import log_job, log_http, log_db, llm_log_context, generate_correlation_id
from app.api.middleware import CorrelationIdMiddleware, get_correlation_id, get_env_from_scope
import structlog
import io
import sys


def test_generate_correlation_id():
    """Тест генерации correlation_id."""
    cid1 = generate_correlation_id()
    cid2 = generate_correlation_id()
    
    # Проверяем, что ID генерируются
    assert isinstance(cid1, str)
    assert len(cid1) > 0
    
    # Проверяем, что ID уникальны
    assert cid1 != cid2


def test_log_job_decorator():
    """Тест декоратора log_job."""
    # Создаем строковый буфер для захвата логов
    log_stream = io.StringIO()
    
    # Настраиваем structlog для вывода в буфер
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
    )
    
    # Создаем тестовую функцию с декоратором
    @log_job("test_job")
    def test_function():
        return "success"
    
    # Вызываем функцию
    result = test_function()
    
    # Проверяем результат
    assert result == "success"
    
    # Проверяем, что логи были записаны
    log_output = log_stream.getvalue()
    assert "job_started" in log_output
    assert "job_finished" in log_output
    assert "test_job" in log_output


def test_log_job_decorator_exception():
    """Тест декоратора log_job при исключении."""
    # Создаем строковый буфер для захвата логов
    log_stream = io.StringIO()
    
    # Настраиваем structlog для вывода в буфер
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
    )
    
    # Создаем тестовую функцию с декоратором, которая бросает исключение
    @log_job("test_job_error")
    def test_function_error():
        raise ValueError("Test error")
    
    # Вызываем функцию и проверяем, что исключение пробрасывается
    with pytest.raises(ValueError):
        test_function_error()
    
    # Проверяем, что логи были записаны
    log_output = log_stream.getvalue()
    assert "job_started" in log_output
    assert "job_finished" in log_output
    assert "test_job_error" in log_output
    assert "Test error" in log_output


def test_log_http_decorator():
    """Тест декоратора log_http."""
    # Создаем строковый буфер для захвата логов
    log_stream = io.StringIO()
    
    # Настраиваем structlog для вывода в буфер
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
    )
    
    # Создаем тестовую функцию с декоратором
    @log_http
    def test_http_call(method="GET", url="http://example.com", **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"test response"
        return mock_response
    
    # Вызываем функцию
    result = test_http_call(method="GET", url="http://example.com")
    
    # Проверяем результат
    assert result.status_code == 200
    assert result.content == b"test response"
    
    # Проверяем, что логи были записаны
    log_output = log_stream.getvalue()
    assert "api_call_start" in log_output
    assert "api_call_end" in log_output
    assert "GET" in log_output
    assert "example.com" in log_output


def test_log_db_decorator():
    """Тест декоратора log_db."""
    # Создаем строковый буфер для захвата логов
    log_stream = io.StringIO()
    
    # Настраиваем structlog для вывода в буфер
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
    )
    
    # Создаем тестовую функцию с декоратором
    @log_db
    def test_db_operation(table="test_table", op="select", **kwargs):
        return [{"id": 1, "name": "test"}]
    
    # Вызываем функцию
    result = test_db_operation(table="test_table", op="select", rows=1)
    
    # Проверяем результат
    assert len(result) == 1
    assert result[0]["id"] == 1
    
    # Проверяем, что логи были записаны
    log_output = log_stream.getvalue()
    assert "db_upsert" in log_output
    assert "test_table" in log_output
    assert "select" in log_output


def test_llm_log_context():
    """Тест функции llm_log_context."""
    context = llm_log_context(
        provider="openai",
        model="gpt-3.5-turbo",
        prompt_hash="abc123",
        input_tokens=100,
        output_tokens=50,
        latency_ms=150.5,
        cache_hit=True,
        budget_remaining=0.8
    )
    
    # Проверяем содержимое контекста
    assert context["provider"] == "openai"
    assert context["model"] == "gpt-3.5-turbo"
    assert context["prompt_hash"] == "abc123"
    assert context["input_tokens"] == 100
    assert context["output_tokens"] == 50
    assert context["latency_ms"] == 150.5
    assert context["cache_hit"] == True
    assert context["budget_remaining"] == 0.8


def test_correlation_id_middleware():
    """Тест middleware для корреляции."""
    # Проверяем, что middleware можно создать
    mock_app = MagicMock()
    middleware = CorrelationIdMiddleware(mock_app)
    assert middleware is not None
    assert middleware.app == mock_app


def test_get_correlation_id():
    """Тест функции get_correlation_id."""
    # Создаем mock request с scope
    mock_request = MagicMock()
    mock_request.scope = {"correlation_id": "test-correlation-id"}
    
    # Получаем correlation_id
    cid = get_correlation_id(mock_request)
    assert cid == "test-correlation-id"


def test_get_env_from_scope():
    """Тест функции get_env_from_scope."""
    # Создаем mock request с scope
    mock_request = MagicMock()
    mock_request.scope = {"env": "test"}
    
    # Получаем окружение
    env = get_env_from_scope(mock_request)
    assert env == "test"