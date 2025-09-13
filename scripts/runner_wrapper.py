#!/usr/bin/env python3
"""
Runner Wrapper - обёртка для запуска orchestrator runner
"""

import os
import sys
import time
import logging
from pathlib import Path

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('runner-wrapper')

def main():
    logger.info("Starting runner wrapper...")
    
    # Проверяем переменные окружения
    required_env = ['DATABASE_URL']
    for var in required_env:
        if not os.environ.get(var):
            logger.error(f"Missing required environment variable: {var}")
            sys.exit(1)
    
    # Пробуем импортировать и запустить runner
    try:
        # Вариант 1: прямой импорт
        from app.services.orchestrator import run_orchestrator_loop
        logger.info("Found orchestrator loop function")
        run_orchestrator_loop()
        
    except ImportError:
        try:
            # Вариант 2: через main app
            from app.main import app
            logger.info("Found main app - running in stub mode")
            
            # Простая заглушка runner
            while True:
                logger.info("Runner tick (stub mode)")
                time.sleep(30)
                
        except ImportError as e:
            logger.error(f"Cannot import required modules: {e}")
            logger.info("Running in minimal mode - just monitoring")
            
            # Минимальный режим - просто мониторинг
            while True:
                logger.info("Minimal runner tick")
                time.sleep(60)

if __name__ == "__main__":
    main()
