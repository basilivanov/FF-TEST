import os
import json
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")


def _stub_llm(monkeypatch, payload):
    from app.api import chat as chat_module

    def fake_completion(*args, **kwargs):
        return {
            "choices": [
                {"message": {"content": json.dumps(payload, ensure_ascii=False)}}
            ]
        }

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)


def test_rest_chat_includes_top_level_action_and_readiness_continue(monkeypatch):
    _prepare_env()
    from app.main import app
    client = TestClient(app)

    _stub_llm(monkeypatch, {
        "response_for_user": "Собрал черновик. Нужна пара уточнений.",
        "action": {"type": "CONTINUE_DIALOG"}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Привет", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()

    # Ожидаем, что в ответе появится верхнеуровневое поле action и readiness_score
    assert "action" in data, "Топ-уровневое поле action должно присутствовать"
    assert data["action"]["type"] == "CONTINUE_DIALOG"
    assert "readiness_score" in data, "Нужно возвращать readiness_score"
    assert 0.0 <= float(data["readiness_score"]) <= 1.0


def test_rest_chat_includes_top_level_action_and_readiness_request_secrets(monkeypatch):
    _prepare_env()
    from app.main import app
    client = TestClient(app)

    _stub_llm(monkeypatch, {
        "response_for_user": "Нужны доступы к Ozon, отправьте через форму.",
        "action": {
            "type": "REQUEST_SECRETS",
            "items": [
                {"key": "OZON_CLIENT_ID", "required": True},
                {"key": "OZON_API_KEY", "required": True}
            ],
            "next": "CONTINUE_DIALOG"
        }
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Интеграция с Ozon", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()

    assert data.get("action", {}).get("type") == "REQUEST_SECRETS"
    items = data.get("action", {}).get("items") or []
    keys = {i.get("key") for i in items}
    assert {"OZON_CLIENT_ID", "OZON_API_KEY"}.issubset(keys)
    assert "readiness_score" in data

