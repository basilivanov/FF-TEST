import os
import json
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    os.environ.pop("TEST_CHAT_FLOW", None)


def test_mask_common_marketplace_tokens(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module

    client = TestClient(app)

    # Подменяем LLM, чтобы ответ всегда был валидным
    def fake_completion(*args, **kwargs):
        return {"choices": [{"message": {"content": json.dumps({
            "response_for_user": "Ок, продолжаем.",
            "action": {"type": "CONTINUE_DIALOG"}
        }, ensure_ascii=False)}}]}

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)

    # Сообщение содержит потенциальные секреты WB/Ozon — должны маскироваться
    text = "WB_API_TOKEN=wb_very_secret_123; OZON_API_KEY=oz_very_secret_456;"
    r = client.post("/api/v1/chat/maintainer", json={"message": text, "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    history_text = json.dumps(data.get("history") or [], ensure_ascii=False)

    # Ожидаем, что сырых значений нет в истории
    assert "wb_very_secret_123" not in history_text
    assert "oz_very_secret_456" not in history_text

    # Ожидаем placeholder’ы
    assert "<SECRET:WB_API_TOKEN>" in history_text
    assert "<SECRET:OZON_API_KEY>" in history_text
