from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_returns_prometheus_text():
    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/plain"
    )
    body = response.text
    # Допускаем пустой ответ, если ещё нет зарегистрированных метрик
    assert response.status_code == 200
    if body.strip():
        assert "#" in body or "=" in body
