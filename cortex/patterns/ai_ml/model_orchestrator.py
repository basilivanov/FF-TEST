#!/usr/bin/env python3
"""
AI/ML модели оркестратор для FeatureFactory.
Управляет различными AI/ML моделями и их интеграцией в процесс разработки.
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import structlog
from datetime import datetime, timedelta
import numpy as np
import hashlib

log = structlog.get_logger()

class ModelType(Enum):
    """Типы AI/ML моделей"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review" 
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    BUG_DETECTION = "bug_detection"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_ANALYSIS = "security_analysis"
    ARCHITECTURE_RECOMMENDATION = "architecture_recommendation"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    CUSTOM = "custom"

class ModelProvider(Enum):
    """Провайдеры AI/ML моделей"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    LOCAL = "local"
    CUSTOM = "custom"

@dataclass
class ModelConfig:
    """Конфигурация AI/ML модели"""
    name: str
    type: ModelType
    provider: ModelProvider
    model_id: str
    endpoint: str
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 120
    cost_per_token: float = 0.0001
    rate_limit: int = 60  # requests per minute
    context_window: int = 8000
    supports_streaming: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)

@dataclass 
class ModelRequest:
    """Запрос к AI/ML модели"""
    prompt: str
    model_type: ModelType
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelResponse:
    """Ответ от AI/ML модели"""
    content: str
    model_name: str
    tokens_used: int
    cost: float
    duration: float
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

class BaseModelClient(ABC):
    """Базовый класс для клиентов AI/ML моделей"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()
        
    async def _create_session(self):
        """Создание HTTP сессии"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        headers = self._get_headers()
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
    
    async def _close_session(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            
    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FeatureFactory-AI-Client/1.0"
        }
        
        if self.config.api_key:
            if self.config.provider == ModelProvider.OPENAI:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            elif self.config.provider == ModelProvider.ANTHROPIC:
                headers["x-api-key"] = self.config.api_key
            elif self.config.provider == ModelProvider.GOOGLE:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        headers.update(self.config.custom_headers)
        return headers
    
    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Генерация контента с помощью модели"""
        pass
    
    @abstractmethod
    def _format_prompt(self, request: ModelRequest) -> Dict[str, Any]:
        """Форматирование промпта для конкретного провайдера"""
        pass

class OpenAIClient(BaseModelClient):
    """Клиент для OpenAI API"""
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        start_time = datetime.now()
        
        payload = self._format_prompt(request)
        
        try:
            async with self.session.post(self.config.endpoint, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                content = data["choices"][0]["message"]["content"]
                tokens_used = data["usage"]["total_tokens"]
                
                duration = (datetime.now() - start_time).total_seconds()
                cost = tokens_used * self.config.cost_per_token
                
                return ModelResponse(
                    content=content,
                    model_name=self.config.name,
                    tokens_used=tokens_used,
                    cost=cost,
                    duration=duration,
                    correlation_id=request.correlation_id,
                    metadata={
                        "provider": self.config.provider.value,
                        "model_id": self.config.model_id,
                        "finish_reason": data["choices"][0].get("finish_reason")
                    }
                )
                
        except Exception as e:
            log.error(
                event="model_generation_error",
                model=self.config.name,
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise
    
    def _format_prompt(self, request: ModelRequest) -> Dict[str, Any]:
        return {
            "model": self.config.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt(request.model_type)
                },
                {
                    "role": "user", 
                    "content": request.prompt
                }
            ],
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or self.config.temperature
        }
    
    def _get_system_prompt(self, model_type: ModelType) -> str:
        """Системный промпт в зависимости от типа модели"""
        prompts = {
            ModelType.CODE_GENERATION: "Ты опытный разработчик. Генерируй чистый, хорошо документированный код.",
            ModelType.CODE_REVIEW: "Ты код-ревьювер. Анализируй код на наличие багов, проблем производительности и нарушений best practices.",
            ModelType.TEST_GENERATION: "Ты специалист по тестированию. Создавай comprehensive тесты с высоким покрытием.",
            ModelType.DOCUMENTATION: "Ты технический писатель. Создавай ясную и полную документацию.",
            ModelType.BUG_DETECTION: "Ты эксперт по поиску багов. Анализируй код и выявляй потенциальные проблемы.",
            ModelType.SECURITY_ANALYSIS: "Ты эксперт по безопасности. Проверяй код на уязвимости и проблемы безопасности.",
            ModelType.ARCHITECTURE_RECOMMENDATION: "Ты архитектор программного обеспечения. Предлагай оптимальные архитектурные решения."
        }
        return prompts.get(model_type, "Ты полезный AI ассистент.")

class AnthropicClient(BaseModelClient):
    """Клиент для Anthropic Claude API"""
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        start_time = datetime.now()
        
        payload = self._format_prompt(request)
        
        try:
            async with self.session.post(self.config.endpoint, json=payload) as response:
                response.raise_for_status() 
                data = await response.json()
                
                content = data["content"][0]["text"]
                tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                
                duration = (datetime.now() - start_time).total_seconds()
                cost = tokens_used * self.config.cost_per_token
                
                return ModelResponse(
                    content=content,
                    model_name=self.config.name,
                    tokens_used=tokens_used,
                    cost=cost,
                    duration=duration,
                    correlation_id=request.correlation_id,
                    metadata={
                        "provider": self.config.provider.value,
                        "model_id": self.config.model_id,
                        "stop_reason": data.get("stop_reason")
                    }
                )
                
        except Exception as e:
            log.error(
                event="model_generation_error",
                model=self.config.name,
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise
    
    def _format_prompt(self, request: ModelRequest) -> Dict[str, Any]:
        return {
            "model": self.config.model_id,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or self.config.temperature,
            "system": self._get_system_prompt(request.model_type),
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        }
        
    def _get_system_prompt(self, model_type: ModelType) -> str:
        # Аналогично OpenAI, но адаптировано для Claude
        prompts = {
            ModelType.CODE_GENERATION: "Ты опытный разработчик. Генерируй чистый, хорошо документированный код следуя лучшим практикам.",
            # ... остальные промпты
        }
        return prompts.get(model_type, "Ты полезный AI ассистент.")

class ModelOrchestrator:
    """Оркестратор AI/ML моделей"""
    
    def __init__(self, model_configs: List[ModelConfig]):
        self.models: Dict[str, BaseModelClient] = {}
        self.model_configs = {config.name: config for config in model_configs}
        self._usage_stats: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Инициализация всех моделей"""
        for config in self.model_configs.values():
            client = self._create_client(config)
            await client._create_session()
            self.models[config.name] = client
            
            # Инициализация статистики
            self._usage_stats[config.name] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
                "errors": 0,
                "avg_duration": 0.0
            }
    
    async def cleanup(self):
        """Очистка ресурсов"""
        for client in self.models.values():
            await client._close_session()
    
    def _create_client(self, config: ModelConfig) -> BaseModelClient:
        """Создание клиента для модели"""
        if config.provider == ModelProvider.OPENAI:
            return OpenAIClient(config)
        elif config.provider == ModelProvider.ANTHROPIC:
            return AnthropicClient(config)
        # Добавить другие провайдеры
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def generate(
        self, 
        request: ModelRequest, 
        model_name: Optional[str] = None
    ) -> ModelResponse:
        """Генерация с автоматическим выбором модели или указанной моделью"""
        
        if model_name:
            model = self.models.get(model_name)
            if not model:
                raise ValueError(f"Model {model_name} not found")
        else:
            model = self._select_best_model(request)
        
        try:
            response = await model.generate(request)
            
            # Обновляем статистику
            stats = self._usage_stats[model.config.name]
            stats["requests"] += 1
            stats["tokens"] += response.tokens_used
            stats["cost"] += response.cost
            stats["avg_duration"] = (stats["avg_duration"] * (stats["requests"] - 1) + response.duration) / stats["requests"]
            
            log.info(
                event="model_generation_success",
                model=model.config.name,
                tokens_used=response.tokens_used,
                duration=response.duration,
                cost=response.cost,
                correlation_id=request.correlation_id
            )
            
            return response
            
        except Exception as e:
            stats = self._usage_stats[model.config.name]
            stats["errors"] += 1
            
            log.error(
                event="model_generation_failed",
                model=model.config.name,
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise
    
    def _select_best_model(self, request: ModelRequest) -> BaseModelClient:
        """Автоматический выбор лучшей модели для задачи"""
        
        # Фильтруем модели по типу
        suitable_models = [
            model for model in self.models.values()
            if model.config.type == request.model_type
        ]
        
        if not suitable_models:
            # Если нет специализированных моделей, берем общие
            suitable_models = [
                model for model in self.models.values()
                if model.config.type == ModelType.CUSTOM
            ]
        
        if not suitable_models:
            # Берем первую доступную
            suitable_models = list(self.models.values())
        
        # Выбираем по критериям: стоимость, производительность, доступность
        best_model = min(suitable_models, key=self._model_score)
        return best_model
    
    def _model_score(self, model: BaseModelClient) -> float:
        """Вычисление скора модели для выбора лучшей"""
        config = model.config
        stats = self._usage_stats[config.name]
        
        # Факторы: стоимость (меньше лучше), скорость (быстрее лучше), надежность (меньше ошибок лучше)
        cost_factor = config.cost_per_token * 1000  # Нормализуем
        speed_factor = stats.get("avg_duration", 1.0)
        error_rate = stats["errors"] / max(stats["requests"], 1)
        
        # Суммарный скор (меньше лучше)
        return cost_factor + speed_factor + error_rate * 10
    
    async def generate_code(
        self, 
        requirements: str, 
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> ModelResponse:
        """Специализированный метод для генерации кода"""
        
        prompt = f"""
Требования: {requirements}

Контекст: {json.dumps(context or {}, ensure_ascii=False, indent=2)}

Сгенерируй код, который:
1. Соответствует всем требованиям
2. Следует best practices
3. Включает обработку ошибок
4. Хорошо документирован
5. Покрыт тестами

Код:
"""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=ModelType.CODE_GENERATION,
            context=context,
            correlation_id=correlation_id
        )
        
        return await self.generate(request)
    
    async def review_code(
        self, 
        code: str, 
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> ModelResponse:
        """Специализированный метод для ревью кода"""
        
        prompt = f"""
Проведи ревью следующего кода:

```
{code}
```

Контекст: {json.dumps(context or {}, ensure_ascii=False, indent=2)}

Проанализируй:
1. Корректность логики
2. Performance проблемы
3. Security уязвимости 
4. Code style и best practices
5. Возможные баги
6. Предложения по улучшению

Результат ревью:
"""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=ModelType.CODE_REVIEW,
            context=context,
            correlation_id=correlation_id
        )
        
        return await self.generate(request)
    
    async def generate_tests(
        self, 
        code: str,
        test_framework: str = "pytest",
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> ModelResponse:
        """Генерация тестов для кода"""
        
        prompt = f"""
Создай comprehensive тесты для следующего кода используя {test_framework}:

```
{code}
```

Контекст: {json.dumps(context or {}, ensure_ascii=False, indent=2)}

Тесты должны включать:
1. Unit тесты для всех функций
2. Edge cases и граничные условия
3. Error handling тесты
4. Integration тесты если нужно
5. Мокирование внешних зависимостей
6. Fixtures для тестовых данных

Достигни coverage > 90%.

Тесты:
"""
        
        request = ModelRequest(
            prompt=prompt,
            model_type=ModelType.TEST_GENERATION,
            context=context,
            correlation_id=correlation_id
        )
        
        return await self.generate(request)
    
    def get_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получение статистики использования моделей"""
        return self._usage_stats.copy()
    
    async def batch_generate(
        self, 
        requests: List[ModelRequest],
        max_concurrent: int = 5
    ) -> List[ModelResponse]:
        """Пакетная генерация с ограничением параллелизма"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_generate(request: ModelRequest) -> ModelResponse:
            async with semaphore:
                return await self.generate(request)
        
        tasks = [limited_generate(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Пример конфигурации
def create_default_orchestrator() -> ModelOrchestrator:
    """Создание оркестратора с базовой конфигурацией"""
    
    configs = [
        # Code generation модель
        ModelConfig(
            name="claude-sonnet-code",
            type=ModelType.CODE_GENERATION,
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-sonnet-20240229",
            endpoint="https://api.anthropic.com/v1/messages",
            cost_per_token=0.00015,
            temperature=0.3  # Более детерминированный для кода
        ),
        
        # Code review модель  
        ModelConfig(
            name="gpt4-code-review",
            type=ModelType.CODE_REVIEW,
            provider=ModelProvider.OPENAI,
            model_id="gpt-4-turbo-preview",
            endpoint="https://api.openai.com/v1/chat/completions",
            cost_per_token=0.00001,
            temperature=0.2
        ),
        
        # Documentation модель
        ModelConfig(
            name="claude-haiku-docs",
            type=ModelType.DOCUMENTATION,
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-haiku-20240307", 
            endpoint="https://api.anthropic.com/v1/messages",
            cost_per_token=0.000025,  # Более дешевая модель для документации
            temperature=0.5
        )
    ]
    
    return ModelOrchestrator(configs)

# Пример использования
async def main():
    """Пример использования AI/ML оркестратора"""
    
    orchestrator = create_default_orchestrator()
    await orchestrator.initialize()
    
    try:
        # Генерация кода
        code_response = await orchestrator.generate_code(
            requirements="Создай функцию для валидации email адресов с использованием regex",
            context={"language": "python", "framework": "pydantic"},
            correlation_id="test-code-gen-001"
        )
        
        print(f"Сгенерированный код:\n{code_response.content}")
        print(f"Использовано токенов: {code_response.tokens_used}")
        print(f"Стоимость: ${code_response.cost:.4f}")
        
        # Ревью сгенерированного кода
        review_response = await orchestrator.review_code(
            code=code_response.content,
            context={"language": "python"},
            correlation_id="test-review-001"
        )
        
        print(f"\nРезультат ревью:\n{review_response.content}")
        
        # Статистика использования
        stats = orchestrator.get_usage_stats()
        for model_name, stat in stats.items():
            print(f"\n{model_name}: {stat}")
            
    finally:
        await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())