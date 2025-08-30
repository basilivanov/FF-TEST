import pytest
from unittest.mock import MagicMock
from app.api.middleware import CorrelationIdMiddleware, get_correlation_id, get_env_from_scope
import uuid


def test_get_correlation_id():
    """Тест функции get_correlation_id."""
    # Создаем mock request с correlation_id в scope
    mock_request = MagicMock()
    mock_request.scope = {"correlation_id": "test-correlation-id"}
    
    # Получаем correlation_id
    cid = get_correlation_id(mock_request)
    assert cid == "test-correlation-id"


def test_get_correlation_id_default():
    """Тест функции get_correlation_id с дефолтным значением."""
    # Создаем mock request без correlation_id
    mock_request = MagicMock()
    mock_request.scope = {}
    
    # Получаем correlation_id (должен сгенерироваться новый)
    cid = get_correlation_id(mock_request)
    assert isinstance(cid, str)
    assert len(cid) > 0


def test_get_env_from_scope():
    """Тест функции get_env_from_scope."""
    # Создаем mock request с env в scope
    mock_request = MagicMock()
    mock_request.scope = {"env": "test"}
    
    # Получаем окружение
    env = get_env_from_scope(mock_request)
    assert env == "test"


def test_get_env_from_scope_default():
    """Тест функции get_env_from_scope с дефолтным значением."""
    # Создаем mock request без env
    mock_request = MagicMock()
    mock_request.scope = {}
    
    # Получаем окружение (должно быть дефолтное)
    env = get_env_from_scope(mock_request)
    assert env == "test"