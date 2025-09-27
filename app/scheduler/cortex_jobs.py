#!/usr/bin/env python3
"""
Планировщик задач для анализа кортекса.
Запускает анализ каждый час и сохраняет результаты.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

# Добавляем путь к модулям приложения
sys.path.append(str(Path(__file__).parent.parent))

from app.services.cortex_analyzer import CortexAnalyzer

# Простое логирование без зависимостей
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_env() -> str:
    """Получает текущее окружение (test или prod)."""
    return os.getenv("ENV", "test")

class CortexScheduler:
    """Планировщик для анализа кортекса"""

    def __init__(self):
        self.analyzer = CortexAnalyzer()

    async def run_hourly_analysis(self):
        """Запускает ежечасный анализ кортекса"""
        try:
            logger.info("Starting scheduled cortex analysis...")

            # Запускаем анализ
            report = self.analyzer.run_analysis()

            # Сохраняем результат
            self.analyzer.save_report(report)

            # Логируем успешное выполнение
            logger.info(f"Cortex scheduled analysis - Score: {report.overall_score:.1f}%, Roles: {len(report.roles)}, Recommendations: {len(report.recommendations)}")

            logger.info(f"Cortex analysis completed. Score: {report.overall_score:.1f}%")

            # Если балл критически низкий, логируем предупреждение
            if report.overall_score < 50:
                critical_roles = [r.role for r in report.roles if r.overall_score < 50]
                logger.warning(f"Critical cortex health! Score: {report.overall_score:.1f}%, Critical roles: {critical_roles}")

        except Exception as e:
            logger.error(f"Failed to run cortex analysis: {e}")

    async def cleanup_old_reports(self, keep_days: int = 30):
        """Очищает старые отчёты (старше keep_days дней)"""
        try:
            import sqlite3
            from datetime import timedelta

            db_path = "/opt/feature-factory/data/cortex_health.db"

            if not Path(db_path).exists():
                return

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Удаляем старые записи
            cursor.execute(
                "DELETE FROM cortex_reports WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            cursor.execute(
                "DELETE FROM role_metrics WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )

            deleted_reports = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_reports > 0:
                logger.info(f"Cleaned up {deleted_reports} old cortex reports")

        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {e}")

def main():
    """Основная функция для одноразового запуска анализа"""
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