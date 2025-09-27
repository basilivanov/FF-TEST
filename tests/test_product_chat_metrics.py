import os
import json
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    os.environ.pop("TEST_CHAT_FLOW", None)


def _stub_llm(monkeypatch, payload):
    from app.api import chat as chat_module

    def fake_completion(*args, **kwargs):
        return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)


def test_product_chat_metrics_increment_for_actions(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    # CONTINUE_DIALOG
    _stub_llm(monkeypatch, {
        "response_for_user": "Ок, продолжаем.",
        "action": {"type": "CONTINUE_DIALOG"}
    })
    r1 = client.post("/api/v1/chat/maintainer", json={"message": "hi", "analyst_type": "BUSINESS"})
    assert r1.status_code == 200

    # REQUEST_SECRETS
    _stub_llm(monkeypatch, {
        "response_for_user": "Нужны доступы.",
        "action": {"type": "REQUEST_SECRETS", "items": [{"key": "OZON_API_KEY"}]}
    })
    r2 = client.post("/api/v1/chat/maintainer", json={"message": "ozon", "analyst_type": "BUSINESS"})
    assert r2.status_code == 200

    # FINALIZE (валидный intent импорт)
    async def fake_create_feature(req, feature_request, db):
        class O: id = 999
        return O()
    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к финализации",
        "action": {
            "type": "FINALIZE_AND_CREATE_FEATURE",
            "intent_payload": {
                "intent": {
                    "type": "marketplace.import",
                    "provider": "ozon",
                    "operation": "sales",
                    "period": {"preset": "last_7d", "timezone": "UTC"},
                    "destination": {"kind": "sheet", "target": "Sales"}
                }
            }
        }
    })
    r3 = client.post("/api/v1/chat/maintainer", json={"message": "finalize", "analyst_type": "BUSINESS"})
    assert r3.status_code == 200

    # Проверяем метрики
    m = client.get("/metrics").text
    assert "product_chat_total" in m
    assert "product_chat_total{action=\"CONTINUE_DIALOG\"}" in m or "product_chat_total{action=\"CONTINUE_DIALOG\"" in m
    assert "product_chat_total{action=\"REQUEST_SECRETS\"}" in m or "product_chat_total{action=\"REQUEST_SECRETS\"" in m
    assert "product_chat_total{action=\"FINALIZE_AND_CREATE_FEATURE\"}" in m or "product_chat_total{action=\"FINALIZE_AND_CREATE_FEATURE\"" in m
    assert "product_chat_readiness_sum" in m
    assert "product_chat_finalize_total" in m
