import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
import httpx

from app.integrations.ozon_client import OzonClient

def test_create_ozon_client():
    """Test creation of Ozon client."""
    client = OzonClient("test_key", "test_secret")
    assert isinstance(client, OzonClient)
    assert client.api_key == "test_key"
    assert client.api_secret == "test_secret"

def test_make_request_success():
    """Test successful HTTP request."""
    client = OzonClient("test_key", "test_secret")
    
    # Мокируем клиент HTTP
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"test": "data"}}
    mock_response.raise_for_status.return_value = None
    
    with patch.object(client.client, 'request', return_value=mock_response):
        response = client._make_request("POST", "/v3/posting/fbs/list", json={"test": "data"})
        assert response == mock_response

def test_make_request_http_error():
    """Test HTTP error handling."""
    client = OzonClient("test_key", "test_secret")
    
    # Мокируем клиент HTTP для возврата ошибки
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 401
    http_error = httpx.HTTPStatusError(
        "Unauthorized", 
        request=Mock(), 
        response=mock_response
    )
    
    with patch.object(client.client, 'request', side_effect=http_error):
        with pytest.raises(httpx.HTTPStatusError):
            client._make_request("POST", "/v3/posting/fbs/list", json={"test": "data"})

def test_close_client():
    """Test closing client."""
    client = OzonClient("test_key", "test_secret")
    
    with patch.object(client.client, 'close') as mock_close:
        client.close()
        mock_close.assert_called_once()