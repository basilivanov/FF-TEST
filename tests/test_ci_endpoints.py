from __future__ import annotations

import hmac
import hashlib
import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ci_status_requires_basic_auth():
    response = client.post("/api/v1/ci/status", json={"context": "tests", "state": "success"})
    assert response.status_code == 401


def test_ci_status_accepts_valid_auth(monkeypatch):
    monkeypatch.setenv("CI_HOOK_USER", "ops")
    monkeypatch.setenv("CI_HOOK_PASS", "ops123")

    with patch("app.api.ci_endpoints.log") as log_mock:
        response = client.post(
            "/api/v1/ci/status",
            json={"context": "tests", "state": "success"},
            auth=("ops", "ops123"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["context"] == "tests"
    events = [call.kwargs["event"] for call in log_mock.info.call_args_list]
    assert "ci_status_received" in events
    assert "ci_status_processed" in events


def test_github_webhook_valid_signature(monkeypatch):
    body = json.dumps({"action": "opened", "number": 42}).encode()
    secret = "supersecret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    with patch("app.api.ci_endpoints.handle_pull_request_event", new_callable=AsyncMock) as handler:
        response = client.post(
            "/api/v1/ci/webhook",
            data=body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": f"sha256={signature}",
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 200
    assert response.json()["event"] == "pull_request"
    handler.assert_awaited_once()


def test_git_env_debug_endpoint(monkeypatch):
    monkeypatch.setenv("GIT_INTEGRATION_ENABLED", "true")
    monkeypatch.setenv("SCM_PUSH_ENABLED", "false")
    monkeypatch.setenv("GITHUB_OWNER", "feature-factory")

    response = client.get("/api/v1/ci/debug/git-env")

    assert response.status_code == 200
    data = response.json()
    assert data["git_integration_enabled"] is True
    assert data["variables"]["GITHUB_OWNER"]["present"] is True
