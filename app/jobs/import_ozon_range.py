#!/usr/bin/env python3
"""
Job for importing raw data from Ozon.
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.integrations.ozon_client import import_ozon_postings
from app.logging_helpers import log_job, log_db

# Настройка логгера
log = structlog.get_logger()

def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        str: Database URL
    """
    return os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")

@log_job("import_ozon_range")
def import_ozon_range(date_from: str, date_to: str, api_key: str, api_secret: str) -> Dict[str, Any]:
    """
    Import Ozon postings for specified date range.
    
    Args:
        date_from (str): Start date in ISO format (YYYY-MM-DD)
        date_to (str): End date in ISO format (YYYY-MM-DD)
        api_key (str): Ozon API key
        api_secret (str): Ozon API secret
        
    Returns:
        Dict[str, Any]: Result of import operation
    """
    try:
        # Парсим даты
        dt_from = datetime.fromisoformat(date_from)
        dt_to = datetime.fromisoformat(date_to)
        
        # Импортируем постинги
        postings = import_ozon_postings(api_key, api_secret, dt_from, dt_to)
        imported_count = len(postings)
        
        # Сохраняем постинги в БД партиями
        batch_size = 100
        for i in range(0, len(postings), batch_size):
            batch = postings[i:i + batch_size]
            save_postings_batch(batch)
            
            # Логируем партию
            log.info(
                event="batch_saved",
                component="job",
                agent_role="Dev",
                kv={
                    "batch_size": len(batch),
                    "total_imported": min(i + len(batch), imported_count)
                }
            )
        
        # Обновляем watermark
        update_watermark("ozon", dt_to)
        
        # Логируем завершение импорта
        log.info(
            event="watermark_advanced",
            component="job",
            agent_role="Dev",
            kv={
                "source": "ozon",
                "watermark": dt_to.isoformat()
            }
        )
        
        return {
            "status": "success",
            "imported_count": imported_count,
            "date_from": date_from,
            "date_to": date_to
        }
            
    except Exception as e:
        log.error(
            event="import_ozon_error",
            component="job",
            agent_role="Dev",
            kv={
                "error": str(e),
                "date_from": date_from,
                "date_to": date_to
            },
            stack=True
        )
        raise

@log_db
def save_postings_batch(postings: List[Dict[str, Any]]) -> None:
    """
    Save batch of postings to database.
    
    Args:
        postings (List[Dict[str, Any]]): List of postings to save
    """
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                for posting in postings:
                    # Upsert posting using ON CONFLICT DO UPDATE
                    conn.execute(text("""
                        INSERT INTO postings_raw (source, posting_id, payload_json, fetched_at, period_from, period_to)
                        VALUES (:source, :posting_id, :payload_json, :fetched_at, :period_from, :period_to)
                        ON CONFLICT (source, posting_id) DO UPDATE SET
                            payload_json = EXCLUDED.payload_json,
                            fetched_at = EXCLUDED.fetched_at,
                            period_from = EXCLUDED.period_from,
                            period_to = EXCLUDED.period_to
                    """), {
                        'source': posting['source'],
                        'posting_id': posting['posting_id'],
                        'payload_json': posting['payload_json'],
                        'fetched_at': posting['fetched_at'],
                        'period_from': posting['period_from'],
                        'period_to': posting['period_to']
                    })
                
                transaction.commit()
                
                # Логируем сохранение партии
                log.info(
                    event="db_upsert",
                    component="db",
                    agent_role="Dev",
                    kv={
                        "table": "postings_raw",
                        "op": "upsert",
                        "rows": len(postings),
                        "conflicts": 0  # В реальной реализации можно подсчитать конфликты
                    }
                )
                
            except Exception as e:
                transaction.rollback()
                raise
                
    except SQLAlchemyError as e:
        log.error(
            event="db_error",
            component="db",
            agent_role="Dev",
            kv={
                "table": "postings_raw",
                "op": "upsert",
                "error": str(e)
            },
            stack=True
        )
        raise

@log_db
def update_watermark(source: str, watermark: datetime) -> None:
    """
    Update watermark for specified source.
    
    Args:
        source (str): Source name
        watermark (datetime): New watermark datetime
    """
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Upsert watermark
            conn.execute(text("""
                INSERT INTO etl_watermarks (source, last_successful_iso)
                VALUES (:source, :watermark)
                ON CONFLICT (source) DO UPDATE SET
                    last_successful_iso = EXCLUDED.last_successful_iso
            """), {
                'source': source,
                'watermark': watermark.isoformat()
            })
            
            # Логируем обновление watermark
            log.info(
                event="db_upsert",
                component="db",
                agent_role="Dev",
                kv={
                    "table": "etl_watermarks",
                    "op": "upsert",
                    "rows": 1,
                    "conflicts": 0
                }
            )
            
    except SQLAlchemyError as e:
        log.error(
            event="db_error",
                component="db",
                agent_role="Dev",
                kv={
                    "table": "etl_watermarks",
                    "op": "upsert",
                    "error": str(e)
                },
                stack=True
            )
        raise

# Функции для CLI использования
def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import Ozon postings")
    parser.add_argument("--date-from", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--date-to", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--api-key", required=True, help="Ozon API key")
    parser.add_argument("--api-secret", required=True, help="Ozon API secret")
    
    args = parser.parse_args()
    
    try:
        result = import_ozon_range(
            args.date_from,
            args.date_to,
            args.api_key,
            args.api_secret
        )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()