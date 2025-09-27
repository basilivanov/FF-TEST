from __future__ import annotations
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.api.telegram_notifications import (
    router, 
    TelegramMessage, 
    TelegramTemplateMessage,
    send_telegram_message_async,
    send_telegram_template_message_async
)

def test_send_message_endpoint_success():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data
    message_data = {
        "chat_id": "123456789",
        "text": "Test message",
        "parse_mode": "HTML"
    }
    
    # Mock successful response from Telegram API
    mock_response = {
        "ok": True,
        "result": {
            "message_id": 1,
            "from": {
                "id": 1234567890,
                "is_bot": True,
                "first_name": "TestBot"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "last_name": "User",
                "type": "private"
            },
            "date": 1612345678,
            "text": "Test message"
        }
    }
    
    with patch("app.api.telegram_notifications.send_telegram_message_async", new=AsyncMock(return_value=mock_response)):
        response = client.post("/api/v1/telegram/send-message", json=message_data)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "result" in data

def test_send_message_endpoint_validation_error():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data with missing required field
    message_data = {
        "text": "Test message"
        # chat_id is missing
    }
    
    response = client.post("/api/v1/telegram/send-message", json=message_data)
    assert response.status_code == 422

def test_send_message_endpoint_telegram_api_error():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data
    message_data = {
        "chat_id": "123456789",
        "text": "Test message"
    }
    
    # Mock HTTPException from Telegram API error
    with patch("app.api.telegram_notifications.send_telegram_message_async", new=AsyncMock(side_effect=HTTPException(status_code=502, detail="Telegram API error: 400"))):
        response = client.post("/api/v1/telegram/send-message", json=message_data)
        assert response.status_code == 502
        assert "Telegram API error" in response.json()["detail"]

def test_send_template_message_endpoint_success():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data
    message_data = {
        "chat_id": "123456789",
        "template": "Hello {name}, your order #{order_id} is {status}",
        "template_data": {
            "name": "John",
            "order_id": "12345",
            "status": "shipped"
        },
        "parse_mode": "Markdown"
    }
    
    # Mock successful response from Telegram API
    mock_response = {
        "ok": True,
        "result": {
            "message_id": 2,
            "from": {
                "id": 1234567890,
                "is_bot": True,
                "first_name": "TestBot"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "last_name": "User",
                "type": "private"
            },
            "date": 1612345679,
            "text": "Hello John, your order #12345 is shipped"
        }
    }
    
    with patch("app.api.telegram_notifications.send_telegram_template_message_async", new=AsyncMock(return_value=mock_response)):
        response = client.post("/api/v1/telegram/send-template-message", json=message_data)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "result" in data

def test_send_template_message_endpoint_validation_error():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data with missing required field
    message_data = {
        "template": "Hello {name}",
        "template_data": {"name": "John"}
        # chat_id is missing
    }
    
    response = client.post("/api/v1/telegram/send-template-message", json=message_data)
    assert response.status_code == 422

def test_send_template_message_endpoint_missing_template_param():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data with missing template parameter
    message_data = {
        "chat_id": "123456789",
        "template": "Hello {name}, your order #{order_id} is {status}",
        "template_data": {
            "name": "John"
            # order_id and status are missing
        }
    }
    
    response = client.post("/api/v1/telegram/send-template-message", json=message_data)
    assert response.status_code == 400
    assert "Missing template parameter" in response.json()["detail"]

def test_send_template_message_endpoint_telegram_api_error():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test data
    message_data = {
        "chat_id": "123456789",
        "template": "Hello {name}",
        "template_data": {"name": "John"}
    }
    
    # Mock HTTPException from Telegram API error
    with patch("app.api.telegram_notifications.send_telegram_template_message_async", new=AsyncMock(side_effect=HTTPException(status_code=502, detail="Telegram API error: 400"))):
        response = client.post("/api/v1/telegram/send-template-message", json=message_data)
        assert response.status_code == 502
        assert "Telegram API error" in response.json()["detail"]