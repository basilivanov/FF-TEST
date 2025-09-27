import os
import json
import asyncio
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    os.environ.pop("TEST_CHAT_FLOW", None)


def _stub_llm(monkeypatch, payload):
    from app.api import chat as chat_module

    def fake_completion(*args, **kwargs):
        return {
            "choices": [
                {"message": {"content": json.dumps(payload, ensure_ascii=False)}}
            ]
        }

    monkeypatch.setattr(chat_module.llm_router, "completion", fake_completion)


def test_readiness_high_for_marketplace_import_complete(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    # Не допустить реального вызова create_feature
    async def fake_create_feature(req, feature_request, db):
        class Obj: id = 123
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "marketplace.import",
        "provider": "ozon",
        "operation": "sales",
        "period": {"preset": "last_7d", "timezone": "UTC"},
        "destination": {"kind": "sheet", "target": "Sales_Ozon"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к запуску.",
        "action": {
            "type": "FINALIZE_AND_CREATE_FEATURE",
            "intent_payload": {"intent": intent}
        }
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Импорт продаж озон", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85


def test_readiness_low_blocks_finalize_when_incomplete(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 1
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    # Отсутствует destination — намеренно неполный intent
    intent = {
        "type": "marketplace.import",
        "provider": "ozon",
        "operation": "sales",
        "period": {"preset": "last_7d"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Пробую финализировать.",
        "action": {
            "type": "FINALIZE_AND_CREATE_FEATURE",
            "intent_payload": {"intent": intent}
        }
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Импорт продаж озон", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    # Должны блокировать финализацию и возвращать CONTINUE_DIALOG
    assert float(data.get("readiness_score") or 1) < 0.85
    assert (data.get("action") or {}).get("type") == "CONTINUE_DIALOG"
    assert called["create_feature"] is False


def test_readiness_reprice_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 777
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "pricing.reprice",
        "marketplaces": ["wildberries", "ozon"],
        "skus": {"source": "sheet", "locator": "Reprice!A:A"},
        "rules": {"target": "parity", "rounding": "1"},
        "poll": {"every": "30m", "tz": "UTC"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к запуску repricing.",
        "action": {
            "type": "FINALIZE_AND_CREATE_FEATURE",
            "intent_payload": {"intent": intent}
        }
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Репрайсинг WB и Ozon", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_telegram_incomplete_blocks_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 1
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    # Нет channels/parse_mode — должно блокировать
    intent = {
        "type": "telegram.notify",
        "template": "Заказ {id} создан",
        "triggers": ["event:new_order"]
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Пробую финализировать телеграм уведомления",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Телеграм алерты", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 1) < 0.85
    assert (data.get("action") or {}).get("type") == "CONTINUE_DIALOG"
    assert called["create_feature"] is False


def test_readiness_gdocs_append_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 42
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "gdocs.append",
        "spreadsheet": {"create_if_missing": True, "title": "FF_Exports", "sheet": "Sheet1"},
        "mapping": {"columns": ["id", "date", "amount"]},
        "data_source": {"kind": "api", "spec": {"endpoint": "https://example/api"}}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к выгрузке в Google Sheets",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Экспорт в Шит", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_avito_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 301
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "classifieds.avito.leads.sync",
        "source": "api",
        "period": {"preset": "last_30d"},
        "destination": {"kind": "sheet", "target": "AvitoLeads"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к синхронизации лидов Avito",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Avito лиды", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_yclients_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 501
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "yclients.sync",
        "company_id": "12345",
        "operation": "appointments",
        "schedule": "0 * * * *",
        "destination": {"kind": "db", "target": "yclients_appointments"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к синхронизации YCLIENTS",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Yclients синк", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_ads_reporting_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 601
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "ads.reporting",
        "provider": "yandex_direct",
        "metrics": ["Clicks", "Impressions"],
        "period": {"preset": "last_30d"},
        "destination": {"kind": "sheet", "target": "AdsReport"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к отчётам по рекламе",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Direct отчёт", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_analytics_fetch_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 701
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "analytics.fetch",
        "metrics": ["visits"],
        "dimensions": ["date"],
        "period": {"preset": "last_30d"},
        "destination": {"kind": "db", "target": "metrica_daily"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к выгрузке метрик",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Метрика", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_forms_capture_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 801
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "forms.capture",
        "source": "webhook",
        "destination": {"kind": "sheet", "target": "Leads"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к приёму лидов через формы",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Формы лиды", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_delivery_status_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 901
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "delivery.status.sync",
        "provider": "cdek",
        "destination": {"kind": "db", "target": "delivery_status"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к синхронизации статусов доставки",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Статусы CDEK", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_payments_reports_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 1001
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "payments.reports",
        "provider": "yookassa",
        "period": {"preset": "last_30d"},
        "destination": {"kind": "sheet", "target": "Payments"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к отчётам по платежам",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "Платежи", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True


def test_readiness_telephony_cdr_complete_allows_finalize(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import chat as chat_module
    client = TestClient(app)

    called = {"create_feature": False}

    async def fake_create_feature(req, feature_request, db):
        called["create_feature"] = True
        class Obj: id = 1101
        return Obj()

    monkeypatch.setattr(chat_module, "create_feature", fake_create_feature)

    intent = {
        "type": "telephony.cdr.fetch",
        "provider": "mango_office",
        "period": {"preset": "last_7d"},
        "destination": {"kind": "db", "target": "cdr_log"}
    }
    _stub_llm(monkeypatch, {
        "response_for_user": "Готово к выгрузке CDR",
        "action": {"type": "FINALIZE_AND_CREATE_FEATURE", "intent_payload": {"intent": intent}}
    })

    r = client.post("/api/v1/chat/maintainer", json={"message": "CDR", "analyst_type": "BUSINESS"})
    assert r.status_code == 200
    data = r.json()
    assert float(data.get("readiness_score") or 0) >= 0.85
    assert called["create_feature"] is True
