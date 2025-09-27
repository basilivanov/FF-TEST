import os
import json
from fastapi.testclient import TestClient


def _prepare_env():
    os.environ.setdefault("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")
    # Убедимся, что env для бота не задан — чтобы проверить fallback
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)


def test_telegram_reads_token_from_secrets(monkeypatch):
    _prepare_env()
    from app.main import app
    from app.api import telegram_notifications as tg
    from app.db.session import SessionLocal
    from app.utils.secret_store import encrypt_value

    # Заготовим секрет в БД
    db = SessionLocal()
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                value_enc TEXT NOT NULL,
                scope TEXT NOT NULL,
                owner TEXT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        enc = encrypt_value("TEST_BOT_TOKEN")
        db.execute(
            """
            INSERT OR REPLACE INTO secrets(key, value_enc, scope, owner, created_at, updated_at)
            VALUES (:k,:v,'test',NULL,datetime('now'),datetime('now'))
            """,
            {"k": "TELEGRAM_BOT_TOKEN", "v": enc},
        )
        db.commit()
    finally:
        db.close()

    # Подменим фактическую отправку, чтобы не ходить в сеть
    async def fake_send(*args, **kwargs):
        class R:
            ok = True
            result = {"message_id": 1}
        return R()

    monkeypatch.setattr(tg, "send_telegram_message_async", fake_send)

    client = TestClient(app)
    r = client.post("/api/v1/telegram/send-message", json={"chat_id": "1", "text": "ping"})

    # Сейчас тест ожидает, что будет fallback к Secret Store
    # До внедрения фичи этот тест упадёт (get_bot_token берёт только env)
    assert r.status_code == 200

