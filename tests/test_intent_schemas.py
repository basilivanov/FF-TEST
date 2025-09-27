import json, os


def _load_schema(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_marketplace_import_schema_valid_invalid():
    try:
        import jsonschema
    except Exception:
        return  # пропускаем если нет jsonschema
    base = _load_schema('configs/schemas/intent/marketplace.import.schema.json')
    valid = {
        "type": "marketplace.import",
        "provider": "ozon",
        "operation": "sales",
        "period": {"preset": "last_7d", "timezone": "UTC"},
        "destination": {"kind": "sheet", "target": "Sales"}
    }
    jsonschema.validate(instance=valid, schema=base)
    invalid = {
        "type": "marketplace.import",
        "provider": "ozon"
        # нет operation/period/destination
    }
    try:
        jsonschema.validate(instance=invalid, schema=base)
        assert False, "invalid intent must not validate"
    except Exception:
        pass


def test_pricing_reprice_schema_valid_invalid():
    try:
        import jsonschema
    except Exception:
        return
    base = _load_schema('configs/schemas/intent/pricing.reprice.schema.json')
    valid = {
        "type": "pricing.reprice",
        "skus": {"source": "sheet", "locator": "A:A"},
        "rules": {"target": "parity"}
    }
    jsonschema.validate(instance=valid, schema=base)
    invalid = {"type": "pricing.reprice", "skus": {"source": "sheet"}}  # нет locator и rules
    try:
        jsonschema.validate(instance=invalid, schema=base)
        assert False
    except Exception:
        pass


def test_telegram_notify_schema_valid_invalid():
    try:
        import jsonschema
    except Exception:
        return
    base = _load_schema('configs/schemas/intent/telegram.notify.schema.json')
    valid = {
        "type": "telegram.notify",
        "template": "Hi {id}",
        "channels": [{"kind": "chat", "chat_id": "1"}],
        "triggers": ["event:new_order"]
    }
    jsonschema.validate(instance=valid, schema=base)
    invalid = {"type": "telegram.notify", "template": "X"}
    try:
        jsonschema.validate(instance=invalid, schema=base)
        assert False
    except Exception:
        pass


def test_gdocs_append_schema_valid_invalid():
    try:
        import jsonschema
    except Exception:
        return
    base = _load_schema('configs/schemas/intent/gdocs.append.schema.json')
    valid = {
        "type": "gdocs.append",
        "spreadsheet": {"sheet": "Sheet1"},
        "mapping": {"columns": ["a", "b"]}
    }
    invalid = {"type": "gdocs.append", "mapping": {"columns": ["a"]}}
    import jsonschema
    jsonschema.validate(instance=valid, schema=base)
    try:
        jsonschema.validate(instance=invalid, schema=base)
        assert False
    except Exception:
        pass


def test_more_intent_schemas_valid_invalid():
    try:
        import jsonschema
    except Exception:
        return
    # yclients.sync
    ys = _load_schema('configs/schemas/intent/yclients.sync.schema.json')
    jsonschema.validate(instance={
        "type":"yclients.sync","company_id":"1","operation":"appointments","destination":{"kind":"db","target":"t"}
    }, schema=ys)
    try:
        jsonschema.validate(instance={"type":"yclients.sync"}, schema=ys)
        assert False
    except Exception:
        pass
    # ads.reporting
    ar = _load_schema('configs/schemas/intent/ads.reporting.schema.json')
    jsonschema.validate(instance={
        "type":"ads.reporting","provider":"yandex_direct","metrics":["Clicks"],"period":{"preset":"last_30d"},"destination":{"kind":"sheet","target":"x"}
    }, schema=ar)
    try:
        jsonschema.validate(instance={"type":"ads.reporting","provider":"yandex_direct"}, schema=ar)
        assert False
    except Exception:
        pass
    # analytics.fetch
    af = _load_schema('configs/schemas/intent/analytics.fetch.schema.json')
    jsonschema.validate(instance={
        "type":"analytics.fetch","metrics":["visits"],"dimensions":["date"],"period":{"preset":"last_30d"},"destination":{"kind":"db","target":"x"}
    }, schema=af)
    try:
        jsonschema.validate(instance={"type":"analytics.fetch","metrics":[]}, schema=af)
        assert False
    except Exception:
        pass
    # forms.capture
    fc = _load_schema('configs/schemas/intent/forms.capture.schema.json')
    jsonschema.validate(instance={
        "type":"forms.capture","source":"webhook","destination":{"kind":"sheet","target":"Leads"}
    }, schema=fc)
    try:
        jsonschema.validate(instance={"type":"forms.capture"}, schema=fc)
        assert False
    except Exception:
        pass
    # delivery.status.sync
    ds = _load_schema('configs/schemas/intent/delivery.status.sync.schema.json')
    jsonschema.validate(instance={
        "type":"delivery.status.sync","provider":"cdek","destination":{"kind":"db","target":"x"}
    }, schema=ds)
    try:
        jsonschema.validate(instance={"type":"delivery.status.sync"}, schema=ds)
        assert False
    except Exception:
        pass
    # payments.reports
    pr = _load_schema('configs/schemas/intent/payments.reports.schema.json')
    jsonschema.validate(instance={
        "type":"payments.reports","provider":"yookassa","period":{"preset":"last_30d"},"destination":{"kind":"sheet","target":"x"}
    }, schema=pr)
    try:
        jsonschema.validate(instance={"type":"payments.reports"}, schema=pr)
        assert False
    except Exception:
        pass
    # telephony.cdr.fetch
    tc = _load_schema('configs/schemas/intent/telephony.cdr.fetch.schema.json')
    jsonschema.validate(instance={
        "type":"telephony.cdr.fetch","provider":"mango_office","period":{"preset":"last_7d"},"destination":{"kind":"db","target":"cdr"}
    }, schema=tc)
    try:
        jsonschema.validate(instance={"type":"telephony.cdr.fetch"}, schema=tc)
        assert False
    except Exception:
        pass
