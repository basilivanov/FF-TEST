import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.index.service import IndexService
import os

# Установим правильную базу данных для тестов
os.environ["DATABASE_URL"] = "sqlite:///./feature.new.db"

# Создаем тестового клиента
client = TestClient(app)

def test_get_symbol():
    """Тест получения информации о символах."""
    # Тестируем получение всех символов
    response = client.get("/api/v1/index/symbol")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    
    # Тестируем получение символов с фильтрацией
    response = client.get("/api/v1/index/symbol?symbol_name=test")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data

def test_get_calls():
    """Тест получения информации о вызовах."""
    # Тестируем получение всех вызовов
    response = client.get("/api/v1/index/calls")
    assert response.status_code == 200
    data = response.json()
    assert "edges" in data
    
    # Тестируем получение вызовов с фильтрацией
    response = client.get("/api/v1/index/calls?source_symbol=test")
    assert response.status_code == 200
    data = response.json()
    assert "edges" in data

def test_get_module_card():
    """Тест получения карточки модуля."""
    # Тестируем получение карточки модуля
    response = client.get("/api/v1/index/module-card?file_path=test.py")
    assert response.status_code == 200
    data = response.json()
    assert "module_card" in data

def test_index_service_get_symbol():
    """Тест метода get_symbol сервиса IndexService."""
    # Создаем экземпляр сервиса
    service = IndexService()
    
    # Тестируем получение всех символов
    symbols = service.get_symbol()
    assert isinstance(symbols, list)
    
    # Тестируем получение символов с фильтрацией
    symbols = service.get_symbol(symbol_name="test")
    assert isinstance(symbols, list)

def test_index_service_get_calls():
    """Тест метода get_calls сервиса IndexService."""
    # Создаем экземпляр сервиса
    service = IndexService()
    
    # Тестируем получение всех вызовов
    edges = service.get_calls()
    assert isinstance(edges, list)
    
    # Тестируем получение вызовов с фильтрацией
    edges = service.get_calls(source_symbol="test")
    assert isinstance(edges, list)

def test_index_service_get_module_card():
    """Тест метода get_module_card сервиса IndexService."""
    # Создаем экземпляр сервиса
    service = IndexService()
    
    # Тестируем получение карточки модуля
    module_card = service.get_module_card("test.py")
    assert isinstance(module_card, dict)

if __name__ == "__main__":
    pytest.main([__file__])