#!/usr/bin/env python3
"""Планировщик задач для анализа кортекса."""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import sqlite3
import sys

sys.path.append(str(Path(__file__).parent.parent))

from app.logging_helpers import log, get_env, generate_correlation_id
from app.services.cortex_analyzer import CortexAnalyzer


def _log(level: str, event: str, run_id: str, **kv) -> None:
    getattr(log, level)(
        event=event,
        env=get_env(),
        component="cortex_scheduler",
        agent_role="Cortex",
        run_id=run_id,
        task_id=run_id,
        correlation_id=run_id,
        kv=kv,
    )


class CortexScheduler:
    """Планировщик для анализа кортекса."""

    def __init__(self):
        self.analyzer = CortexAnalyzer()

    async def run_hourly_analysis(self) -> None:
        """Запускает ежечасный анализ кортекса."""

        analysis_id = generate_correlation_id()
        try:
            _log("info", "cortex_scheduler_analysis_started", analysis_id)

            report = self.analyzer.run_analysis(analysis_id=analysis_id)
            self.analyzer.save_report(report, analysis_id=analysis_id)

            _log(
                "info",
                "cortex_scheduler_analysis_completed",
                analysis_id,
                overall_score=report.overall_score,
                roles=len(report.roles),
            )

            if report.overall_score < 50:
                critical_roles = [r.role for r in report.roles if r.overall_score < 50]
                _log(
                    "warning",
                    "cortex_scheduler_analysis_critical",
                    analysis_id,
                    overall_score=report.overall_score,
                    critical_roles=critical_roles,
                )
        except Exception as exc:  # pragma: no cover
            _log(
                "error",
                "cortex_scheduler_analysis_failed",
                analysis_id,
                err_type=type(exc).__name__,
                err_msg=str(exc),
            )

    async def cleanup_old_reports(self, keep_days: int = 30) -> None:
        """Очищает старые отчёты (старше keep_days дней)."""

        job_id = generate_correlation_id()
        try:
            db_path = "/opt/feature-factory/data/cortex_health.db"
            if not Path(db_path).exists():
                _log("info", "cortex_scheduler_cleanup_skipped", job_id, reason="db_missing")
                return

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cortex_reports WHERE timestamp < ?", (cutoff_date.isoformat(),))
            deleted_reports = cursor.rowcount
            cursor.execute("DELETE FROM role_metrics WHERE timestamp < ?", (cutoff_date.isoformat(),))
            deleted_roles = cursor.rowcount
            conn.commit()
            conn.close()

            _log(
                "info",
                "cortex_scheduler_cleanup_completed",
                job_id,
                reports_deleted=deleted_reports,
                role_rows_deleted=deleted_roles,
            )
        except Exception as exc:  # pragma: no cover
            _log(
                "error",
                "cortex_scheduler_cleanup_failed",
                job_id,
                err_type=type(exc).__name__,
                err_msg=str(exc),
            )


def main() -> None:
    """Основная функция для одноразового запуска анализа."""

    import argparse

    parser = argparse.ArgumentParser(description="Cortex Analysis Scheduler")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old reports")
    parser.add_argument("--keep-days", type=int, default=30, help="Days to keep reports")

    args = parser.parse_args()

    scheduler = CortexScheduler()
    if args.cleanup:
        asyncio.run(scheduler.cleanup_old_reports(args.keep_days))
    else:
        asyncio.run(scheduler.run_hourly_analysis())


if __name__ == "__main__":
    main()
