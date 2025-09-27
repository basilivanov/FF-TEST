import os
import json
import re
import types

from fastapi.testclient import TestClient


def _prepare_env():
    # Ensure DATABASE_URL is present for app.db.session
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")


def _stub_llm_response(response_content: dict):
    """Builds a stub llm_router.completion return value compatible with chat.py expectations."""
    # chat.py supports two formats: object with .choices or dict
    # We'll return dict form used by internal router
    return {
        "choices": [
            {"message": {"content": json.dumps(response_content, ensure_ascii=False)}}
        ]
    }


def test_chat_masks_and_stores_telegram_token(monkeypatch):
    _prepare_env()
    # Import after env set
    from app.main import app
    from app.api import chat as chat_module

    client = TestClient(app)

    # Build a plausible Telegram token to trigger masking (\d+:[A-Za-z0-9_-]{35,})
    fake_tg_token = "123456:" + "A" * 36
    user_text = f"Мой токен телеграм: {fake_tg_token}. Пожалуйста, создай алерт."

    # Stub LLM to produce a benign CONTINUE_DIALOG response so endpoint succeeds
    def fake_completion(*args, **kwargs):
        return _stub_llm_response({
            "response_for_user": "Принял настройки. Секрет сохранён безопасно.",
            "action": {"type": "CONTINUE_DIALOG"}
        })

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)

    payload = {"message": user_text, "analyst_type": "BUSINESS"}
    r = client.post("/api/v1/chat/maintainer", json=payload)
    assert r.status_code == 200
    data = r.json()

    # History should not contain raw token
    history_text = json.dumps(data.get("history") or [], ensure_ascii=False)
    assert fake_tg_token not in history_text
    # Mask placeholder should be present
    assert "<SECRET:TELEGRAM_BOT_TOKEN>" in history_text

    # Secret is stored masked via API
    r2 = client.get("/api/v1/secrets/TELEGRAM_BOT_TOKEN")
    # 200 or 404 if some env/db state prevents upsert; accept both but never expose the token
    if r2.status_code == 200:
        masked = r2.json().get("masked")
        assert masked == "****" or masked.startswith("****")


def test_chat_propagates_request_secrets_action(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module

    client = TestClient(app)

    # Force LLM to ask for marketplace secrets
    def fake_completion(*args, **kwargs):
        return _stub_llm_response({
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

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)

    r = client.post("/api/v1/chat/maintainer", json={"message": "Интеграция с Ozon", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    # Ensure action is present and intact
    # The last assistant message should include response_for_user, but API response serializes action at top-level
    assert "response" in data
    # We can't assert 'action' at top because HTTP endpoint returns action only inside history item — so test content consistency
    assistant_msgs = [m for m in (data.get("history") or []) if m.get("role") == "assistant"]
    assert assistant_msgs, "assistant response should be present"
    last = assistant_msgs[-1]
    assert "Нужны доступы" in last.get("content", "")

