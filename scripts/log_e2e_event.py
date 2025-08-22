#!/usr/bin/env python3
"""
Логирование событий E2E регрессии
"""

import sys
import json
import uuid
from datetime import datetime
import structlog

# Настройка логирования согласно стандарту Logging-001
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def log_e2e_event(event_type, **kwargs):
    """Логирование E2E события согласно стандарту Logging-001"""
    correlation_id = str(uuid.uuid4())
    
    # Базовая структура лога согласно Logging-001
    log_entry = {
        "ts": datetime.utcnow().isoformat(),
        "level": "INFO",
        "env": "TEST",
        "component": "ci_pipeline",
        "agent_role": "E2E_Regression",
        "run_id": None,
        "task_id": None, 
        "correlation_id": correlation_id,
        "event": event_type,
        "kv": kwargs
    }
    
    logger.info(event_type, **log_entry)
    
    # Также выводим в stdout для CI
    print(json.dumps(log_entry, ensure_ascii=False))

def main():
    """Основная функция логирования"""
    if len(sys.argv) < 2:
        print("Usage: python log_e2e_event.py <event_type> [key=value] [key=value] ...")
        print("Example: python log_e2e_event.py e2e_regression_nightly status=completed duration=120")
        sys.exit(1)
    
    event_type = sys.argv[1]
    
    # Парсинг дополнительных параметров
    kwargs = {}
    for arg in sys.argv[2:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Попытка преобразовать в число
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Оставляем как строку
            kwargs[key] = value
    
    log_e2e_event(event_type, **kwargs)

if __name__ == '__main__':
    main()