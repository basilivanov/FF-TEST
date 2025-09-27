#!/usr/bin/env python3
"""
FeatureFactory Runner - Background task processor
"""
import asyncio
import logging
import time
from app.orchestrator.loop import get_orchestrator_loop

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main runner loop"""
    logger.info("Starting FeatureFactory Runner")
    
    try:
        # Получаем экземпляр оркестратора
        loop = get_orchestrator_loop()
        
        # Основной цикл обработки задач
        while True:
            try:
                # Обрабатываем бэклог задач
                await loop._process_backlog()
                
                # Ждем 2 секунды перед следующей итерацией
                await asyncio.sleep(2)
            except KeyboardInterrupt:
                logger.info("Runner stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in runner loop: {e}", exc_info=True)
                # Ждем перед повторной попыткой
                await asyncio.sleep(5)
                
    except Exception as e:
        logger.error(f"Failed to start runner: {e}", exc_info=True)
        return 1
        
    logger.info("FeatureFactory Runner stopped")
    return 0

if __name__ == "__main__":
    asyncio.run(main())