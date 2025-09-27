import os
import json
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    os.environ.pop("TEST_CHAT_FLOW", None)


def test_extended_secret_masking(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    def fake_completion(*args, **kwargs):
        return {"choices": [{"message": {"content": json.dumps({
            "response_for_user": "Ок.",
            "action": {"type": "CONTINUE_DIALOG"}
        }, ensure_ascii=False)}}]}

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)

    text = (
        "AVITO_CLIENT_ID=av1; AVITO_CLIENT_SECRET=av2; "
        "YCLIENTS_API_KEY=yc1; YCLIENTS_PARTNER_TOKEN=yc2; "
        "DIRECT_API_TOKEN=yd1; VK_ADS_TOKEN=vk1; METRICA_TOKEN=ym1; GA4_CREDENTIALS_JSON=ga1; "
        "YOOKASSA_SECRET_KEY=yk1; TINKOFF_TERMINAL_KEY=tk1; TINKOFF_PASSWORD=tp1; "
        "CDEK_CLIENT_ID=cd1; CDEK_CLIENT_SECRET=cd2; BOXBERRY_TOKEN=bb1; "
        "MANGO_TOKEN=mg1; ZADARMA_KEY=zd1; ZADARMA_SECRET=zd2; SMS_RU_API_KEY=sms1; ONEC_AUTH=oc1;"
    )
    r = client.post("/api/v1/chat/maintainer", json={"message": text, "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    h = json.dumps(r.json().get("history") or [], ensure_ascii=False)

    # Ни одного сырого значения
    for raw in ["av1","av2","yc1","yc2","yd1","vk1","ym1","ga1","yk1","tk1","tp1","cd1","cd2","bb1","mg1","zd1","zd2","sms1","oc1"]:
        assert raw not in h
    # Плейсхолдеры на месте
    for key in [
        "AVITO_CLIENT_ID","AVITO_CLIENT_SECRET","YCLIENTS_API_KEY","YCLIENTS_PARTNER_TOKEN",
        "DIRECT_API_TOKEN","VK_ADS_TOKEN","METRICA_TOKEN","GA4_CREDENTIALS_JSON",
        "YOOKASSA_SECRET_KEY","TINKOFF_TERMINAL_KEY","TINKOFF_PASSWORD",
        "CDEK_CLIENT_ID","CDEK_CLIENT_SECRET","BOXBERRY_TOKEN",
        "MANGO_TOKEN","ZADARMA_KEY","ZADARMA_SECRET","SMS_RU_API_KEY","ONEC_AUTH"
    ]:
        assert f"<SECRET:{key}>" in h
