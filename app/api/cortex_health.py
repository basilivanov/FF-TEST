#!/usr/bin/env python3
"""API эндпоинты для мониторинга здоровья кортекса."""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.logging_helpers import log, get_env, generate_correlation_id
from app.services.cortex_analyzer import CortexAnalyzer, CortexHealthReport

router = APIRouter(prefix="/cortex")


def _log(level: str, event: str, correlation_id: str, task_id: str, **kv: Any) -> None:
    getattr(log, level)(
        event=event,
        env=get_env(),
        component="cortex_api",
        agent_role="Cortex",
        run_id=correlation_id,
        task_id=task_id,
        correlation_id=correlation_id,
        kv=kv,
    )


def get_db_path() -> str:
    """Возвращает путь к БД с отчётами о здоровье кортекса."""

    return "/opt/feature-factory/data/cortex_health.db"


@router.get("/health")
async def get_cortex_health(request: Request) -> Dict[str, Any]:
    """Возвращает свежий отчёт по здоровью кортекса (с пересчётом при необходимости)."""

    correlation_id = request.headers.get("x-correlation-id", generate_correlation_id())
    task_id = str(uuid.uuid4())
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cortex_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                overall_score REAL NOT NULL,
                report_data TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            SELECT timestamp, overall_score, report_data
            FROM cortex_reports
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            timestamp_str, overall_score, report_raw = row
            timestamp = datetime.fromisoformat(timestamp_str)
            age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()

            if age_seconds < 3600:
                _log(
                    "info",
                    "cortex_health_cached",
                    correlation_id,
                    task_id,
                    overall_score=overall_score,
                    age_seconds=round(age_seconds, 2),
                )
                return format_health_response(json.loads(report_raw))

        analyzer = CortexAnalyzer()
        report = analyzer.run_analysis(analysis_id=correlation_id)
        analyzer.save_report(report, db_path, analysis_id=correlation_id)

        _log(
            "info",
            "cortex_health_recomputed",
            correlation_id,
            task_id,
            overall_score=report.overall_score,
            roles=len(report.roles),
        )
        return format_health_response(report)

    except Exception as exc:  # pragma: no cover
        _log(
            "error",
            "cortex_health_error",
            correlation_id,
            task_id,
            err_type=type(exc).__name__,
            err_msg=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get cortex health: {exc}") from exc


@router.post("/analyze")
async def trigger_analysis(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Запускает асинхронный анализ кортекса."""

    correlation_id = generate_correlation_id()
    task_id = str(uuid.uuid4())

    def run_analysis() -> None:
        analysis_task_id = str(uuid.uuid4())
        try:
            analyzer = CortexAnalyzer()
            report = analyzer.run_analysis(analysis_id=correlation_id)
            analyzer.save_report(report, get_db_path(), analysis_id=correlation_id)
            _log(
                "info",
                "cortex_analysis_triggered",
                correlation_id,
                analysis_task_id,
                overall_score=report.overall_score,
                roles=len(report.roles),
            )
        except Exception as exc:  # pragma: no cover
            _log(
                "error",
                "cortex_analysis_background_error",
                correlation_id,
                analysis_task_id,
                err_type=type(exc).__name__,
                err_msg=str(exc),
            )

    _log("info", "cortex_analysis_enqueued", correlation_id, task_id)
    background_tasks.add_task(run_analysis)
    return {"status": "Analysis started", "correlation_id": correlation_id}


@router.get("/history")
async def get_health_history(request: Request, days: Optional[int] = 7) -> Dict[str, Any]:
    """Возвращает историю отчётов за указанное количество дней."""

    correlation_id = request.headers.get("x-correlation-id", generate_correlation_id())
    task_id = str(uuid.uuid4())

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        since_date = datetime.now(timezone.utc) - timedelta(days=days or 7)
        cursor.execute(
            """
            SELECT timestamp, overall_score
            FROM cortex_reports
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (since_date.isoformat(),),
        )
        reports = cursor.fetchall()

        cursor.execute(
            """
            SELECT timestamp, role, overall_score
            FROM role_metrics
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (since_date.isoformat(),),
        )
        role_metrics = cursor.fetchall()
        conn.close()

        history = {
            "period_days": days or 7,
            "overall_trend": [
                {"timestamp": ts, "score": score}
                for ts, score in reports
            ],
            "role_trends": {},
        }

        for ts, role, score in role_metrics:
            history["role_trends"].setdefault(role, []).append({"timestamp": ts, "score": score})

        _log(
            "info",
            "cortex_history_returned",
            correlation_id,
            task_id,
            period_days=history["period_days"],
            points=len(history["overall_trend"]),
        )
        return history

    except Exception as exc:  # pragma: no cover
        _log(
            "error",
            "cortex_history_error",
            correlation_id,
            task_id,
            err_type=type(exc).__name__,
            err_msg=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get history: {exc}") from exc


@router.get("/roles/{role}")
async def get_role_details(role: str, request: Request) -> Dict[str, Any]:
    """Возвращает детали анализа по конкретной роли."""

    correlation_id = request.headers.get("x-correlation-id", generate_correlation_id())
    task_id = str(uuid.uuid4())

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT report_data
            FROM cortex_reports
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            _log("warning", "cortex_role_report_missing", correlation_id, task_id, role=role)
            raise HTTPException(status_code=404, detail="No cortex reports found")

        report = json.loads(row[0])
        for role_analysis in report.get("roles", []):
            if role_analysis.get("role") == role:
                _log("info", "cortex_role_details_returned", correlation_id, task_id, role=role)
                return role_analysis

        _log("warning", "cortex_role_not_found", correlation_id, task_id, role=role)
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        _log(
            "error",
            "cortex_role_error",
            correlation_id,
            task_id,
            role=role,
            err_type=type(exc).__name__,
            err_msg=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get role details: {exc}") from exc


@router.get("/coverage")
async def get_system_coverage(request: Request) -> Dict[str, Any]:
    """Возвращает покрытие системных компонентов."""

    correlation_id = request.headers.get("x-correlation-id", generate_correlation_id())
    task_id = str(uuid.uuid4())

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT report_data
            FROM cortex_reports
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            analyzer = CortexAnalyzer()
            coverage = analyzer.analyze_system_coverage()
            _log("info", "cortex_coverage_generated", correlation_id, task_id, sources=len(coverage))
            return {"system_coverage": coverage}

        report = json.loads(row[0])
        payload = {
            "system_coverage": report.get("system_coverage", {}),
            "timestamp": report.get("timestamp"),
        }
        _log("info", "cortex_coverage_returned", correlation_id, task_id, sources=len(payload["system_coverage"]))
        return payload

    except Exception as exc:  # pragma: no cover
        _log(
            "error",
            "cortex_coverage_error",
            correlation_id,
            task_id,
            err_type=type(exc).__name__,
            err_msg=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get coverage: {exc}") from exc


def format_health_response(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Форматирует данные отчёта для UI."""

    def to_plain(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: to_plain(v) for k, v in value.items()}
        if isinstance(value, list):
            return [to_plain(v) for v in value]
        if hasattr(value, "__dict__"):
            return {k: to_plain(v) for k, v in value.__dict__.items()}
        return value

    report_dict = to_plain(report_data)
    roles = report_dict.get("roles", []) or []

    formatted_roles = []
    role_icons = {
        "architect": "Users",
        "dev": "Code",
        "qa": "TestTube",
        "scribe": "BookOpen",
        "maintainer": "Wrench",
    }

    for role in roles:
        role_dict = to_plain(role) if not isinstance(role, dict) else {k: to_plain(v) for k, v in role.items()}

        cortex_files = role_dict.get("cortex_files", []) or []
        prompt_files = role_dict.get("prompt_files", []) or []
        last_updated_candidates = [item.get("last_modified") for item in cortex_files + prompt_files if isinstance(item, dict)]
        last_updated = (
            max(last_updated_candidates)
            if last_updated_candidates
            else datetime.now(timezone.utc).isoformat()
        )

        formatted_role = {
            "role": (role_dict.get("role") or "unknown").capitalize(),
            "context_quality": round(role_dict.get("overall_score", 0) or 0),
            "docs_count": len(cortex_files) + len(prompt_files),
            "last_updated": last_updated,
            "issues": role_dict.get("issues", []) or [],
            "icon": role_icons.get(role_dict.get("role"), "FileText"),
        }
        formatted_roles.append(formatted_role)

    overall_score = round(report_dict.get("overall_score", 0) or 0)

    return {
        "overall_score": overall_score,
        "context_freshness": overall_score,
        "role_coverage": len([r for r in formatted_roles if r["context_quality"] > 70]),
        "knowledge_completeness": overall_score,
        "last_updated": report_dict.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "roles": formatted_roles,
        "recommendations": report_dict.get("recommendations", []) or [],
    }
