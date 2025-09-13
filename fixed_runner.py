#!/usr/bin/env python3
"""
Fixed Runner - исправленный orchestrator runner
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменные окружения
os.environ['DATABASE_URL'] = 'sqlite:////opt/feature-factory/data/test.db'

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fixed-runner')

async def run_orchestrator():
    """Запуск orchestrator с правильными настройками."""
    logger.info("Starting fixed orchestrator runner...")
    
    try:
        from app.orchestrator.loop import get_orchestrator_loop
        
        loop = get_orchestrator_loop()
        logger.info("Orchestrator loop created successfully")
        
        # Запускаем цикл обработки
        while True:
            try:
                logger.info("Running orchestrator cycle...")
                await loop._process_backlog()
                await asyncio.sleep(10)  # Пауза между циклами
                
            except Exception as e:
                logger.error(f"Error in orchestrator cycle: {e}")
                await asyncio.sleep(5)  # Короткая пауза при ошибке
                
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(run_orchestrator())