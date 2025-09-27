from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi.testclient import TestClient

from app.main import app
from app.services.cortex_analyzer import CortexHealthReport, RoleAnalysis, FileAnalysis


client = TestClient(app)
BASE_PATH = "/api/v1/cortex"


def _make_report() -> CortexHealthReport:
    now = datetime.now(timezone.utc)
    role = RoleAnalysis(
        role="dev",
        cortex_files=[
            FileAnalysis(
                path="/tmp/doc.md",
                size=10,
                lines=2,
                last_modified=now,
                content_hash="abc",
                content_quality=90.0,
            )
        ],
        prompt_files=[],
        doc_coverage=0.9,
        context_completeness=0.9,
        content_freshness=0.9,
        overall_score=92.0,
        issues=["Все ок"],
    )

    return CortexHealthReport(
        timestamp=now,
        overall_score=88.0,
        roles=[role],
        system_coverage={"docs": 0.9},
        recommendations=["Добавить тесты"],
    )


def _save_report(report: CortexHealthReport, db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cortex_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            overall_score REAL NOT NULL,
            report_data TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS role_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            overall_score REAL NOT NULL
        )
        """
    )
    payload = json.dumps(report, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o))
    conn.execute(
        "INSERT INTO cortex_reports (timestamp, overall_score, report_data) VALUES (?, ?, ?)",
        (report.timestamp.isoformat(), report.overall_score, payload),
    )
    for role in report.roles:
        conn.execute(
            "INSERT INTO role_metrics (timestamp, role, overall_score) VALUES (?, ?, ?)",
            (report.timestamp.isoformat(), role.role, role.overall_score),
        )
    conn.commit()
    conn.close()


def test_cortex_health_endpoint(monkeypatch, tmp_path):
    db_path = tmp_path / "cortex.db"
    report = _make_report()

    def fake_analyzer_factory():
        class FakeAnalyzer:
            def run_analysis(self, analysis_id=None):
                return report

            def save_report(self, report_obj, target, analysis_id=None):
                _save_report(report_obj, Path(target))

        return FakeAnalyzer()

    monkeypatch.setattr("app.api.cortex_health.get_db_path", lambda: str(db_path))
    monkeypatch.setattr("app.api.cortex_health.CortexAnalyzer", fake_analyzer_factory)

    response = client.get(f"{BASE_PATH}/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_score"] == 88
    assert payload["roles"][0]["role"] == "Dev"

    # повторный вызов должен читать сохранённый отчёт без запуска анализатора
    monkeypatch.setattr("app.api.cortex_health.CortexAnalyzer", lambda: None)
    second = client.get(f"{BASE_PATH}/health")
    assert second.status_code == 200
    assert second.json()["overall_score"] == 88


def test_cortex_history_and_role_endpoints(monkeypatch, tmp_path):
    db_path = tmp_path / "cortex.db"
    report = _make_report()
    _save_report(report, db_path)

    monkeypatch.setattr("app.api.cortex_health.get_db_path", lambda: str(db_path))

    history = client.get(f"{BASE_PATH}/history", params={"days": 1})
    assert history.status_code == 200
    hist_payload = history.json()
    assert hist_payload["period_days"] == 1
    assert hist_payload["overall_trend"]

    role = client.get(f"{BASE_PATH}/roles/dev")
    assert role.status_code == 200
    role_payload = role.json()
    assert role_payload["role"] == "dev"
    assert role_payload["overall_score"] == 92.0
