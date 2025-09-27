#!/usr/bin/env python3
"""
E2E-тест средней сложности без моков/стабов:
- Поднимает FastAPI-приложение в тестовом процессе
- Готовит чистую SQLite-базу через Alembic
- Создаёт фичу с autostart+strict
- Ждёт завершения пайплайна (статус DONE в таблице features)

Требования окружения:
- Реальные CLI провайдеров LLM согласно configs/llm_routing.yaml (как минимум первый в цепочке Architect)
- Валидные токены/логины для этих CLI

Если нужного CLI нет — тест помечается как SKIPPED.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


TEST_DB = Path("/tmp/ff_e2e_medium.db")

# Ensure project root is importable
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _have_required_cli() -> bool:
    """Проверяем наличие первого провайдера из цепочки Architect (обычно gemini).
    Можно упростить до проверки любой из известных CLI.
    """
    candidates = [
        "/usr/local/bin/gemini",
        "/usr/local/bin/codex",
        "/usr/local/bin/claude",
        "/usr/local/bin/qwen",
    ]
    return any(os.path.exists(p) and os.access(p, os.X_OK) for p in candidates)


@pytest.mark.e2e
def test_e2e_medium_feature_end_to_end():
    if not _have_required_cli():
        pytest.skip("LLM CLI not available; skipping real E2E test")

    # Готовим чистую БД
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except Exception:
            pass

    os.environ["ENV"] = "TEST"
    os.environ["DATABASE_URL"] = f"sqlite:////{TEST_DB}"

    # Миграции Alembic
    alembic = Path(".venv/bin/alembic")
    if not alembic.exists():
        pytest.skip("alembic not available in .venv; skip E2E")
    r = subprocess.run([str(alembic), "-c", "alembic.ini", "upgrade", "head"], capture_output=True, text=True)
    assert r.returncode == 0, f"alembic upgrade failed: {r.stderr}"

    # Импортируем приложение только после установки ENV/DATABASE_URL
    from app.main import app

    client = TestClient(app)

    # Запрос: средняя фича (простые API + базовые acceptance в intent)
    payload = {
        "title": "E2E Medium Feature",
        "intent": {
            "title": "Add Hello endpoint and small refinements",
            # acceptance можно оставить пустым — TestSynth/QA покроют базовые оракулы,
            # но при желании можно добавить минимальные примеры:
            "acceptance": {
                "api": [
                    {"method": "GET", "path": "/api/v1/hello?name=Alice", "expected_status": 200}
                ]
            }
        },
        "autostart": True,
        "strict": True,
    }

    resp = client.post("/api/v1/orchestrator/features", json=payload)
    assert resp.status_code == 200, resp.text
    feature_id = resp.json().get("id")
    assert feature_id, "no feature id returned"

    # Ждём завершения пайплайна: статус features должен стать DONE
    # Подключаемся к БД напрямую и опрашиваем таблицу features
    import sqlite3

    deadline = time.time() + 300  # до 5 минут на прогон, зависит от LLM
    last_status = None
    while time.time() < deadline:
        try:
            with sqlite3.connect(TEST_DB) as conn:
                row = conn.execute("SELECT status FROM features WHERE id = ?", (feature_id,)).fetchone()
                if row:
                    last_status = row[0]
                    if last_status == "DONE":
                        break
        except Exception:
            pass
        time.sleep(3)

    assert last_status == "DONE", f"feature not DONE (last_status={last_status})"
