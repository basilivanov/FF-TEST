#!/usr/bin/env python3
"""
API эндпоинты для мониторинга здоровья кортекса.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import sqlite3
import json
from pathlib import Path

from app.services.cortex_analyzer import CortexAnalyzer, CortexHealthReport
import logging
import os

logger = logging.getLogger(__name__)

def get_env() -> str:
    """Получает текущее окружение (test или prod)."""
    return os.getenv("ENV", "test")

router = APIRouter(prefix="/cortex")

def get_db_path() -> str:
    """Получает путь к БД с отчётами о здоровье кортекса"""
    return "/opt/feature-factory/data/cortex_health.db"

@router.get("/health")
async def get_cortex_health() -> Dict[str, Any]:
    """
    Получает последний отчёт о здоровье кортекса.
    Если отчёт старше часа, запускает новый анализ.
    """
    try:
        db_path = get_db_path()

        # Проверяем есть ли свежий отчёт
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Создаём таблицы если их нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cortex_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                overall_score REAL NOT NULL,
                report_data TEXT NOT NULL
            )
        ''')

        # Ищем последний отчёт
        cursor.execute('''
            SELECT timestamp, overall_score, report_data
            FROM cortex_reports
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            timestamp_str, overall_score, report_data = row
            timestamp = datetime.fromisoformat(timestamp_str)

            # Проверяем свежесть отчёта (не старше часа)
            if datetime.now(timezone.utc) - timestamp < timedelta(hours=1):
                report = json.loads(report_data)

                # Формируем ответ в формате UI
                return format_health_response(report)

        # Если отчёта нет или он устарел, запускаем анализ
        analyzer = CortexAnalyzer()
        report = analyzer.run_analysis()
        analyzer.save_report(report, db_path)

        logger.info(f"Cortex analysis - Score: {report.overall_score:.1f}%, Roles: {len(report.roles)}")

        return format_health_response(report.__dict__)

    except Exception as e:
        logger.error(f"Cortex health error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cortex health: {str(e)}")

@router.post("/analyze")
async def trigger_analysis(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Запускает анализ кортекса в фоновом режиме"""

    def run_analysis():
        try:
            analyzer = CortexAnalyzer()
            report = analyzer.run_analysis()
            analyzer.save_report(report, get_db_path())

            logger.info(f"Cortex analysis triggered - Score: {report.overall_score:.1f}%")
        except Exception as e:
            logger.error(f"Cortex analysis error: {e}")

    background_tasks.add_task(run_analysis)
    return {"status": "Analysis started", "message": "Cortex analysis is running in background"}

@router.get("/history")
async def get_health_history(days: Optional[int] = 7) -> Dict[str, Any]:
    """Получает историю здоровья кортекса за указанное количество дней"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Вычисляем дату начала
        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Получаем общие отчёты
        cursor.execute('''
            SELECT timestamp, overall_score
            FROM cortex_reports
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        ''', (since_date.isoformat(),))

        reports = cursor.fetchall()

        # Получаем метрики по ролям
        cursor.execute('''
            SELECT timestamp, role, overall_score
            FROM role_metrics
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        ''', (since_date.isoformat(),))

        role_metrics = cursor.fetchall()
        conn.close()

        # Форматируем данные
        history = {
            "period_days": days,
            "overall_trend": [
                {
                    "timestamp": ts,
                    "score": score
                }
                for ts, score in reports
            ],
            "role_trends": {}
        }

        # Группируем метрики по ролям
        for ts, role, score in role_metrics:
            if role not in history["role_trends"]:
                history["role_trends"][role] = []
            history["role_trends"][role].append({
                "timestamp": ts,
                "score": score
            })

        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/roles/{role}")
async def get_role_details(role: str) -> Dict[str, Any]:
    """Получает детальную информацию о конкретной роли"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем последний отчёт
        cursor.execute('''
            SELECT report_data
            FROM cortex_reports
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="No cortex reports found")

        report = json.loads(row[0])

        # Ищем информацию о роли
        role_data = None
        for role_analysis in report.get("roles", []):
            if role_analysis["role"] == role:
                role_data = role_analysis
                break

        if not role_data:
            raise HTTPException(status_code=404, detail=f"Role '{role}' not found")

        return role_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get role details: {str(e)}")

@router.get("/coverage")
async def get_system_coverage() -> Dict[str, Any]:
    """Получает информацию о покрытии системных компонентов"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем последний отчёт
        cursor.execute('''
            SELECT report_data
            FROM cortex_reports
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if not row:
            # Если отчёта нет, запускаем анализ
            analyzer = CortexAnalyzer()
            coverage = analyzer.analyze_system_coverage()
            return {"system_coverage": coverage}

        report = json.loads(row[0])
        return {
            "system_coverage": report.get("system_coverage", {}),
            "timestamp": report.get("timestamp")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coverage: {str(e)}")

def format_health_response(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Форматирует данные отчёта для UI"""

    # Если report_data - это объект отчёта, конвертируем в dict
    if hasattr(report_data, '__dict__'):
        report_data = report_data.__dict__

    roles = report_data.get("roles", [])

    # Форматируем роли для UI
    formatted_roles = []
    for role in roles:
        # Если role - это объект, конвертируем в dict
        if hasattr(role, '__dict__'):
            role_dict = role.__dict__
        else:
            role_dict = role

        # Определяем иконку для роли
        role_icons = {
            "architect": "Users",
            "dev": "Code",
            "qa": "TestTube",
            "scribe": "BookOpen",
            "maintainer": "Wrench"
        }

        formatted_role = {
            "role": role_dict["role"].capitalize(),
            "context_quality": round(role_dict.get("overall_score", 0)),
            "docs_count": len(role_dict.get("cortex_files", [])) + len(role_dict.get("prompt_files", [])),
            "last_updated": max(
                [f.get("last_modified", "") for f in role_dict.get("cortex_files", []) + role_dict.get("prompt_files", [])]
                or [datetime.now(timezone.utc).isoformat()]
            ),
            "issues": role_dict.get("issues", []),
            "icon": role_icons.get(role_dict["role"], "FileText")
        }
        formatted_roles.append(formatted_role)

    return {
        "overall_score": round(report_data.get("overall_score", 0)),
        "context_freshness": round(report_data.get("overall_score", 0)),  # Упрощённо используем общий балл
        "role_coverage": len([r for r in formatted_roles if r["context_quality"] > 70]),
        "knowledge_completeness": round(report_data.get("overall_score", 0)),  # Упрощённо
        "last_updated": report_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "roles": formatted_roles,
        "recommendations": report_data.get("recommendations", [])
    }