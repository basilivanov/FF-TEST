import os
import json
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    os.environ.pop("TEST_CHAT_FLOW", None)


def test_product_chat_e2e_flow(monkeypatch):
    """Интеграционный e2e: запрос → REQUEST_SECRETS → upsert → финализация."""
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    # Сценарный stub LLM: по тексту сообщения отдаём разные action
    def fake_completion(role: str, messages: list, **kwargs):
        last = messages[-1]["content"] if messages else ""
        if "секрет" in last.lower() or "интеграция" in last.lower():
            return {
                "choices": [{"message": {"content": json.dumps({
                    "response_for_user": "Нужны доступы к Ozon, отправьте через форму.",
                    "action": {
                        "type": "REQUEST_SECRETS",
                        "items": [
                            {"key": "OZON_CLIENT_ID", "required": True},
                            {"key": "OZON_API_KEY", "required": True}
                        ],
                        "next": "CONTINUE_DIALOG"
                    }
                }, ensure_ascii=False)}}]
            }
        # Иначе финализируем валидным intent
        return {
            "choices": [{"message": {"content": json.dumps({
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
            }, ensure_ascii=False)}}]
        }

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)

    # Шаг 1: Запрос → ожидание REQUEST_SECRETS
    r1 = client.post("/api/v1/chat/maintainer", json={"message": "Интеграция с Ozon, нужны секреты", "analyst_type": "BUSINESS"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert (d1.get("action") or {}).get("type") == "REQUEST_SECRETS"
    # readiness ~ 0.5 на этом шаге
    assert float(d1.get("readiness_score") or 0) <= 0.6

    # Шаг 2: Отправка секретов (маскировано)
    # OZON_CLIENT_ID и OZON_API_KEY — упрощенно кладем фиктивные значения
    client.post("/api/v1/secrets/upsert", json={"key": "OZON_CLIENT_ID", "value": "id-123", "scope": "test"})
    client.post("/api/v1/secrets/upsert", json={"key": "OZON_API_KEY", "value": "key-abc", "scope": "test"})

    # Шаг 3: Просим финализировать
    # Подменим create_feature, чтобы не трогать реальные цепочки
    async def fake_create_feature(req, feature_request, db):
        class O: id = 555
        return O()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    r2 = client.post("/api/v1/chat/maintainer", json={"message": "Готово, финализируй", "analyst_type": "BUSINESS"})
    assert r2.status_code == 200
    d2 = r2.json()
    # Проверяем readiness и что ассистент ответил успешно (история содержит сообщение о создании)
    assert float(d2.get("readiness_score") or 0) >= 0.85
    text = json.dumps(d2.get("history") or [], ensure_ascii=False)
    assert "Ваша задача успешно зарегистрирована" in text
