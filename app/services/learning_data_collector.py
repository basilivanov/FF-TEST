#!/usr/bin/env python3
"""
Learning Data Collector для сбора обучающих примеров из реальной работы системы.
Интегрируется с orchestrator для записи результатов выполнения фич.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
import structlog
import os

# Импортируем Learning Engine без ML зависимостей
try:
    import sys
    sys.path.append('/opt/feature-factory/cortex/patterns/ai_ml')
    from learning_engine import LearningExample, LearningType, LearningEngine
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

log = structlog.get_logger()

class LearningDataCollector:
    """Сборщик данных для обучения Learning Engine"""
    
    def __init__(self, data_dir: str = "/opt/feature-factory/data/learning"):
        self.data_dir = data_dir
        self.examples_file = os.path.join(data_dir, "learning_examples.jsonl")
        self.learning_engine = None
        
        # Создаем директорию если не существует
        os.makedirs(data_dir, exist_ok=True)
        
        if ML_AVAILABLE:
            try:
                self.learning_engine = LearningEngine()
                log.info("learning_engine_initialized")
            except Exception as e:
                log.warning("learning_engine_init_failed", error=str(e))
    
    async def collect_feature_result(
        self,
        feature_id: int,
        task_description: str,
        agent_role: str,
        input_features: Dict[str, Any],
        output_result: Dict[str, Any],
        success: bool,
        performance_metrics: Dict[str, float],
        correlation_id: str
    ):
        """Собирает результат выполнения фичи для обучения"""
        
        # Определяем тип обучения на основе результата
        learning_type = self._determine_learning_type(agent_role, success, output_result)
        
        # Создаем пример для обучения
        example_data = {
            "id": f"feature_{feature_id}_{correlation_id}",
            "type": learning_type.value if ML_AVAILABLE else "unknown",
            "input_features": input_features,
            "output_result": output_result,
            "success": success,
            "performance_metrics": performance_metrics,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": correlation_id,
            "metadata": {
                "feature_id": feature_id,
                "agent_role": agent_role,
                "task_description": task_description
            }
        }
        
        # Сохраняем в файл
        await self._save_example(example_data)
        
        # Если ML доступно, добавляем в Learning Engine
        if ML_AVAILABLE and self.learning_engine:
            try:
                example = LearningExample(
                    id=example_data["id"],
                    type=learning_type,
                    input_features=input_features,
                    output_result=output_result,
                    success=success,
                    performance_metrics=performance_metrics,
                    timestamp=datetime.fromisoformat(example_data["timestamp"]),
                    correlation_id=correlation_id,
                    metadata=example_data["metadata"]
                )
                
                await self.learning_engine.learn_from_example(example)
                log.info("learning_example_processed", 
                        example_id=example.id,
                        success=success,
                        learning_type=learning_type.value)
                
            except Exception as e:
                log.error("learning_example_failed", error=str(e))
        
        log.info("learning_data_collected",
                feature_id=feature_id,
                success=success,
                agent_role=agent_role,
                correlation_id=correlation_id)
    
    def _determine_learning_type(self, agent_role: str, success: bool, output_result: Dict[str, Any]) -> 'LearningType':
        """Определяет тип обучения на основе контекста"""
        
        if not ML_AVAILABLE:
            return "unknown"
        
        # Ошибки
        if not success:
            return LearningType.ERROR_PATTERN
        
        # Успешные паттерны по ролям
        role_mapping = {
            "Architect": LearningType.ARCHITECTURE_IMPROVEMENT,
            "Dev": LearningType.CODE_QUALITY,
            "QA": LearningType.TESTING_STRATEGY,
            "Gate": LearningType.CODE_QUALITY,
            "Apply": LearningType.PERFORMANCE_OPTIMIZATION,
            "Scribe": LearningType.SUCCESS_PATTERN
        }
        
        return role_mapping.get(agent_role, LearningType.SUCCESS_PATTERN)
    
    async def _save_example(self, example_data: Dict[str, Any]):
        """Сохраняет пример в JSONL файл"""
        try:
            with open(self.examples_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(example_data, ensure_ascii=False) + '\n')
        except Exception as e:
            log.error("save_example_failed", error=str(e))
    
    async def load_historical_data(self) -> List[Dict[str, Any]]:
        """Загружает исторические данные обучения"""
        examples = []
        
        if not os.path.exists(self.examples_file):
            return examples
        
        try:
            with open(self.examples_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        example = json.loads(line)
                        examples.append(example)
        except Exception as e:
            log.error("load_historical_data_failed", error=str(e))
        
        return examples
    
    async def train_learning_engine(self) -> bool:
        """Тренирует Learning Engine на исторических данных"""
        
        if not ML_AVAILABLE or not self.learning_engine:
            log.warning("learning_engine_unavailable")
            return False
        
        # Загружаем исторические данные
        historical_data = await self.load_historical_data()
        
        if len(historical_data) < 5:
            log.warning("insufficient_training_data", count=len(historical_data))
            return False
        
        try:
            # Конвертируем в LearningExample объекты
            examples = []
            for data in historical_data:
                example = LearningExample(
                    id=data["id"],
                    type=LearningType(data["type"]),
                    input_features=data["input_features"],
                    output_result=data["output_result"],
                    success=data["success"],
                    performance_metrics=data["performance_metrics"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    correlation_id=data["correlation_id"],
                    metadata=data.get("metadata", {})
                )
                examples.append(example)
            
            # Пакетное обучение
            await self.learning_engine.batch_learn(examples)
            
            log.info("learning_engine_trained", 
                    examples_count=len(examples),
                    patterns_detected=len(self.learning_engine.pattern_detector.patterns))
            
            return True
            
        except Exception as e:
            log.error("learning_engine_training_failed", error=str(e))
            return False
    
    async def get_recommendations_for_task(self, task_context: Dict[str, Any]) -> List[str]:
        """Получает рекомендации Learning Engine для задачи"""
        
        if not ML_AVAILABLE or not self.learning_engine:
            # Возвращаем базовые рекомендации без ML
            return self._get_fallback_recommendations(task_context)
        
        try:
            recommendations = self.learning_engine.get_recommendations(task_context)
            return recommendations
        except Exception as e:
            log.warning("get_recommendations_failed", error=str(e))
            return self._get_fallback_recommendations(task_context)
    
    def _get_fallback_recommendations(self, task_context: Dict[str, Any]) -> List[str]:
        """Базовые рекомендации без ML"""
        
        recommendations = []
        task = task_context.get('task', '').lower()
        role = task_context.get('role', '')
        
        # Паттерн-based рекомендации
        if 'api' in task or 'endpoint' in task:
            recommendations.extend([
                "Используйте FastAPI для создания endpoints",
                "Добавьте Pydantic схемы для валидации",
                "Не забудьте про error handling и logging",
                "Создайте unit тесты для API"
            ])
        
        if 'database' in task or 'db' in task or 'migration' in task:
            recommendations.extend([
                "Используйте Alembic для миграций БД", 
                "Следуйте existing database naming conventions",
                "Добавьте индексы для performance",
                "Протестируйте migration rollback"
            ])
        
        if 'test' in task and role == 'QA':
            recommendations.extend([
                "Используйте Playwright для E2E тестов",
                "Добавьте coverage reporting",
                "Создайте fixtures для тестовых данных",
                "Проверьте error scenarios"
            ])
        
        if 'deploy' in task or 'release' in task and role == 'Apply':
            recommendations.extend([
                "Используйте zero-downtime deployment",
                "Проверьте health endpoints перед переключением",
                "Создайте rollback план",
                "Проведите smoke tests после деплоя"
            ])
        
        return recommendations[:5]  # Ограничиваем до 5 рекомендаций
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """Получает статистику обучения"""
        
        historical_data = await self.load_historical_data()
        
        stats = {
            "total_examples": len(historical_data),
            "success_rate": 0.0,
            "examples_by_role": {},
            "examples_by_type": {},
            "recent_examples": 0
        }
        
        if not historical_data:
            return stats
        
        # Статистика успешности
        successful = sum(1 for ex in historical_data if ex.get("success", False))
        stats["success_rate"] = successful / len(historical_data)
        
        # По ролям
        for example in historical_data:
            role = example.get("metadata", {}).get("agent_role", "unknown")
            stats["examples_by_role"][role] = stats["examples_by_role"].get(role, 0) + 1
        
        # По типам обучения
        for example in historical_data:
            ex_type = example.get("type", "unknown")
            stats["examples_by_type"][ex_type] = stats["examples_by_type"].get(ex_type, 0) + 1
        
        # Недавние примеры (за последние 7 дней)
        week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
        for example in historical_data:
            try:
                ex_time = datetime.fromisoformat(example["timestamp"]).timestamp()
                if ex_time > week_ago:
                    stats["recent_examples"] += 1
            except:
                pass
        
        return stats

# Integration с Orchestrator
async def integrate_with_orchestrator():
    """Интеграция с Orchestrator для автоматического сбора данных"""
    
    collector = LearningDataCollector()
    
    # Пример интеграции - это нужно добавить в orchestrator/loop.py
    example_integration = '''
    # В orchestrator/loop.py после завершения выполнения фичи:
    
    from app.services.learning_data_collector import LearningDataCollector
    
    async def on_feature_completed(self, feature_id, result):
        collector = LearningDataCollector()
        
        await collector.collect_feature_result(
            feature_id=feature_id,
            task_description=result.get("description", ""),
            agent_role=result.get("agent_role", ""),
            input_features={
                "requirements": result.get("requirements", []),
                "context": result.get("context", {}),
                "language": result.get("language", "python")
            },
            output_result={
                "artifacts": result.get("artifacts", []),
                "code_generated": result.get("code", ""),
                "tests_created": result.get("tests", ""),
                "error_message": result.get("error", "")
            },
            success=result.get("success", False),
            performance_metrics={
                "execution_time": result.get("execution_time", 0.0),
                "code_quality_score": result.get("quality_score", 0.0),
                "test_coverage": result.get("coverage", 0.0)
            },
            correlation_id=result.get("correlation_id", "")
        )
    '''
    
    log.info("orchestrator_integration_example", code=example_integration)
    return collector

if __name__ == "__main__":
    # Тест collector
    async def test_collector():
        collector = LearningDataCollector()
        
        # Добавляем тестовый пример
        await collector.collect_feature_result(
            feature_id=123,
            task_description="Create health check API endpoint",
            agent_role="Dev",
            input_features={
                "requirements": ["FastAPI endpoint", "Database check"],
                "language": "python"
            },
            output_result={
                "code": "def health_check(): return {'status': 'ok'}",
                "tests": "def test_health_check(): assert True"
            },
            success=True,
            performance_metrics={
                "execution_time": 5.2,
                "code_quality_score": 0.85
            },
            correlation_id="test_001"
        )
        
        # Получаем рекомендации
        recommendations = await collector.get_recommendations_for_task({
            'task': 'Create new API endpoint',
            'role': 'Dev'
        })
        
        print("Рекомендации Learning Engine:")
        for rec in recommendations:
            print(f"- {rec}")
        
        # Статистика
        stats = await collector.get_learning_stats()
        print(f"\nСтатистика обучения: {stats}")
    
    asyncio.run(test_collector())