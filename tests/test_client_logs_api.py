from __future__ import annotations

import json
from unittest.mock import patch, mock_open

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_client_log_ingest_post(tmp_path):
    payload = {
        "level": "error",
        "message": "UI failed",
        "stack": "TypeError: boom",
        "url": "/dashboard",
        "ui_version": "1.2.3",
        "extra": {"widget": "graph"}
    }

    fake_file = tmp_path / "client_logs.jsonl"

    with (
        patch("app.api.client_logs.os.makedirs") as makedirs,
        patch("app.api.client_logs.open", mock_open()) as mock_file,
        patch("app.api.client_logs.get_env", return_value="test"),
        patch("app.api.client_logs.generate_correlation_id", return_value="corr-123"),
        patch("app.api.client_logs.log") as log_mock,
    ):
        response = client.post("/api/v1/logs/client", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["corr_id"] == "corr-123"

    makedirs.assert_called_once()
    mock_file.assert_called()  # ensure запись в jsonl попыталась произойти
    log_mock.error.assert_called_once()  # уровень error → log.error


def test_client_log_ingest_alt_route(tmp_path):
    payload = {"message": "Warn", "level": "warning"}

    with (
        patch("app.api.client_logs.os.makedirs"),
        patch("app.api.client_logs.open", mock_open()),
        patch("app.api.client_logs.get_env", return_value="test"),
        patch("app.api.client_logs.generate_correlation_id", return_value="corr-456"),
        patch("app.api.client_logs.log") as log_mock,
    ):
        response = client.get(
            "/api/v1/client-logs",
            params={"level": "warning", "message": "Warn", "ui_version": "test"}
        )

    assert response.status_code == 200
    assert response.json()["corr_id"] == "corr-456"
    log_mock.warning.assert_called_once()


def test_client_log_recent_reads_file(tmp_path):
    log_path = tmp_path / "client_logs.jsonl"
    records = [
        {"ts": 1, "message": "A"},
        {"ts": 2, "message": "B"}
    ]
    log_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    with patch("app.api.client_logs.os.path.exists", return_value=True), patch(
        "app.api.client_logs.open", mock_open(read_data=log_path.read_text(encoding="utf-8"))
    ):
        response = client.get("/api/v1/logs/client/recent", params={"limit": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert [item["message"] for item in data["items"]] == ["A", "B"]


def test_client_log_recent_when_missing_file():
    with patch("app.api.client_logs.os.path.exists", return_value=False):
        response = client.get("/api/v1/client-logs/recent")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}
