from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.api.notifications import router, TelegramMessage


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def sample_message():
    return TelegramMessage(chat_id=123456789, text="Test message")


def test_send_telegram_notification_success(client, sample_message):
    with patch('app.api.notifications.send_telegram_message_with_retry', new_callable=AsyncMock) as mock_send:
        mock_send.return_value.ok = True
        mock_send.return_value.result = {"message_id": 1}
        
        response = client.post(
            "/api/v1/notifications/telegram",
            json=sample_message.dict(),
            headers={"bot_token": "test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Message sent" in data["message"]


def test_send_telegram_notification_api_error(client, sample_message):
    with patch('app.api.notifications.send_telegram_message_with_retry', new_callable=AsyncMock) as mock_send:
        mock_send.return_value.ok = False
        mock_send.return_value.error_code = 400
        mock_send.return_value.description = "Bad Request: chat not found"
        
        response = client.post(
            "/api/v1/notifications/telegram",
            json=sample_message.dict(),
            headers={"bot_token": "invalid_token"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Bad Request: chat not found" in data["detail"]


def test_send_telegram_notification_internal_error(client, sample_message):
    with patch('app.api.notifications.send_telegram_message_with_retry', new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("Network error")
        
        response = client.post(
            "/api/v1/notifications/telegram",
            json=sample_message.dict(),
            headers={"bot_token": "test_token"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to send notification" in data["detail"]