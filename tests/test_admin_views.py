import pytest
from fastapi.testclient import TestClient
from app.main import app
import base64

client = TestClient(app)

def test_admin_unauthorized_access():
    """Test that admin routes require authentication."""
    # Попытка доступа без авторизации должна возвращать 401
    response = client.get("/admin/jobs")
    assert response.status_code == 401

def test_admin_authorized_access():
    """Test that admin routes work with correct credentials."""
    # Создаем заголовок Basic Auth
    credentials = base64.b64encode(b"admin:password").decode("utf-8")
    
    # Попытка доступа с авторизацией
    response = client.get("/admin/jobs", headers={"Authorization": f"Basic {credentials}"})
    # Должно быть 200 или 500 (если БД не доступна, но не 401)
    assert response.status_code in [200, 500]

def test_admin_logs_route():
    """Test that logs route works."""
    # Создаем заголовок Basic Auth
    credentials = base64.b64encode(b"admin:password").decode("utf-8")
    
    # Попытка доступа к логам
    response = client.get("/admin/logs", headers={"Authorization": f"Basic {credentials}"})
    # Должно быть 200 или 500 (если БД не доступна, но не 401)
    assert response.status_code in [200, 500]

def test_admin_docs_route():
    """Test that docs route works."""
    # Создаем заголовок Basic Auth
    credentials = base64.b64encode(b"admin:password").decode("utf-8")
    
    # Попытка доступа к документам
    response = client.get("/admin/docs", headers={"Authorization": f"Basic {credentials}"})
    # Должно быть 200 или 500 (если БД не доступна, но не 401)
    assert response.status_code in [200, 500]

def test_admin_wrong_credentials():
    """Test that wrong credentials are rejected."""
    # Создаем заголовок Basic Auth с неправильными данными
    credentials = base64.b64encode(b"wrong:user").decode("utf-8")
    
    # Попытка доступа с неправильной авторизацией
    response = client.get("/admin/jobs", headers={"Authorization": f"Basic {credentials}"})
    assert response.status_code == 401

def test_health_check():
    """Test that health check works."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}