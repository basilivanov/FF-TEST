#!/usr/bin/env python3
"""
Модуль для учета токенов LLM и логирования.
"""

import tiktoken
import yaml
import os
from typing import Optional, Dict, Any, Tuple
from datetime import date
import structlog
from app.logging_helpers import log
from app.llm.token_stats import get_token_stats
import hashlib

# Настройка логгера
logger = structlog.get_logger()

# Путь к конфигурационному файлу бюджетов
BUDGETS_CONFIG_PATH = "/opt/feature-factory/configs/llm_budgets.yaml"

class TokenAccountant:
    """Класс для учета токенов LLM."""
    
    def __init__(self):
        """Инициализирует счетчик токенов."""
        self.encoders = {}
        self.token_stats = get_token_stats()
        self.budgets = self._load_budgets_config()
    
    def _load_budgets_config(self) -> Dict[str, int]:
        """Загружает конфигурацию бюджетов из файла."""
        try:
            if not os.path.exists(BUDGETS_CONFIG_PATH):
                logger.error("budgets_config_not_found", path=BUDGETS_CONFIG_PATH)
                return {}
            
            with open(BUDGETS_CONFIG_PATH, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error("budgets_config_load_failed", error=str(e))
            return {}
    
    def get_encoder(self, model: str) -> Optional[tiktoken.Encoding]:
        """
        Получает энкодер для модели.
        
        Args:
            model (str): Название модели
            
        Returns:
            Optional[tiktoken.Encoding]: Энкодер для модели или None если не поддерживается
        """
        try:
            if model not in self.encoders:
                # Пытаемся получить энкодер для модели
                if model.startswith("gpt-"):
                    self.encoders[model] = tiktoken.encoding_for_model(model)
                elif model.startswith("claude-"):
                    # Для Claude используем энкодер gpt-3.5-turbo как приближение
                    self.encoders[model] = tiktoken.encoding_for_model("gpt-3.5-turbo")
                elif model.startswith("qwen-"):
                    # Для Qwen используем энкодер gpt-3.5-turbo как приближение
                    self.encoders[model] = tiktoken.encoding_for_model("gpt-3.5-turbo")
                else:
                    # Пытаемся получить энкодер по умолчанию
                    self.encoders[model] = tiktoken.get_encoding("cl100k_base")
            
            return self.encoders[model]
        except Exception as e:
            logger.error("token_encoder_error", error=str(e), model=model)
            return None
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Подсчитывает количество токенов в тексте для указанной модели.
        
        Args:
            text (str): Текст для подсчета токенов
            model (str): Название модели
            
        Returns:
            int: Количество токенов
        """
        try:
            encoder = self.get_encoder(model)
            if encoder is None:
                return 0
            
            tokens = encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error("token_count_error", error=str(e), model=model, text_length=len(text))
            return 0
    
    def estimate_tokens(self, provider: str, model: str, messages: list) -> Tuple[int, int]:
        """
        Оценивает количество токенов для сообщений.
        
        Args:
            provider (str): Провайдер LLM
            model (str): Название модели
            messages (list): Список сообщений
            
        Returns:
            Tuple[int, int]: (оценка входных токенов, оценка выходных токенов)
        """
        try:
            # Формируем текст из сообщений для подсчета токенов
            prompt_text = ""
            for msg in messages:
                prompt_text += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
            
            # Подсчитываем входные токены
            input_tokens = self.count_tokens(prompt_text, model)
            
            # Для оценки выходных токенов используем эвристику: 
            # средняя длина ответа составляет около 100 токенов
            # или 1.5x от входных токенов, в зависимости от модели
            if model.startswith(("gpt-", "claude-")):
                output_tokens = max(50, int(input_tokens * 1.5))
            else:
                output_tokens = 100
                
            return (input_tokens, output_tokens)
        except Exception as e:
            logger.error("token_estimate_error", error=str(e), provider=provider, model=model)
            # Возвращаем минимальную оценку в случае ошибки
            return (10, 50)
    
    def can_spend(self, role: str, est_in: int, est_out: int) -> Tuple[bool, Optional[int]]:
        """
        Проверяет, можно ли выполнить вызов с учетом бюджета.
        
        Args:
            role (str): Роль агента
            est_in (int): Оценка входных токенов
            est_out (int): Оценка выходных токенов
            
        Returns:
            Tuple[bool, Optional[int]]: (True/False, оставшийся бюджет или None)
        """
        try:
            # Получаем лимит для роли
            limit = self.budgets.get(role)
            if limit is None:
                logger.warning("role_budget_limit_not_found", role=role)
                # Если лимит не найден, разрешаем вызов
                return (True, None)
            
            # Получаем текущую статистику за сегодня
            today = date.today()
            daily_stats = self.token_stats.get_daily_stats(today)
            
            # Считаем использованные токены за сегодня для роли
            used_tokens = 0
            if role in daily_stats:
                for model_data in daily_stats[role].values():
                    used_tokens += model_data.get("input_tokens", 0) + model_data.get("output_tokens", 0)
            
            # Считаем общие токены для этого вызова
            total_tokens = est_in + est_out
            
            # Проверяем, не превысит ли вызов лимит
            remaining = limit - used_tokens
            if total_tokens > remaining:
                return (False, remaining)
            
            return (True, remaining)
        except Exception as e:
            logger.error("budget_check_error", error=str(e), role=role, est_in=est_in, est_out=est_out)
            # В случае ошибки разрешаем вызов
            return (True, None)
    
    def record_usage(self, role: str, provider: str, model: str, in_tokens: int, out_tokens: int, 
                     estimated: bool = False, day: Optional[date] = None):
        """
        Записывает использование токенов.
        
        Args:
            role (str): Роль агента
            provider (str): Провайдер LLM
            model (str): Название модели
            in_tokens (int): Количество входных токенов
            out_tokens (int): Количество выходных токенов
            estimated (bool): Флаг, указывающий, что значения оценочные
            day (Optional[date]): Дата для записи (по умолчанию сегодня)
        """
        try:
            if day is None:
                day = date.today()
            
            # Записываем статистику токенов
            self.token_stats.record_tokens(role, model, in_tokens, out_tokens)
            
            # Логируем запись использования
            logger.info(
                "token_usage_recorded",
                component="llm",
                role=role,
                provider=provider,
                model=model,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                estimated=estimated,
                date=day.isoformat() if day else None
            )
        except Exception as e:
            logger.error("token_usage_record_error", error=str(e), role=role, provider=provider, 
                         model=model, in_tokens=in_tokens, out_tokens=out_tokens, estimated=estimated)
    
    def log_llm_call(self, provider: str, model: str, prompt: str, response: str, 
                     agent_role: str, budget_remaining: Optional[float] = None,
                     prompt_id: Optional[str] = None, prompt_sha256: Optional[str] = None,
                     run_id: Optional[str] = None, usage: Optional[Dict[str, Any]] = None,
                     finish_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Логирует LLM вызов с учетом токенов.
        
        Args:
            provider (str): Провайдер LLM
            model (str): Название модели
            prompt (str): Промпт
            response (str): Ответ
            agent_role (str): Роль агента
            budget_remaining (Optional[float]): Оставшийся бюджет
            prompt_id (Optional[str]): ID промпта
            prompt_sha256 (Optional[str]): SHA256 хэш промпта
            run_id (Optional[str]): ID запуска
            usage (Optional[Dict[str, Any]]): Информация об использовании токенов
            finish_reason (Optional[str]): Причина завершения генерации
            
        Returns:
            Dict[str, Any]: Контекст для логирования
        """
        # Подсчитываем токены
        input_tokens = self.count_tokens(prompt, model)
        output_tokens = self.count_tokens(response, model)
        
        # Вычисляем SHA256 промпта, если не передан
        if prompt_sha256 is None:
            import hashlib
            prompt_sha256 = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

        # Записываем статистику токенов
        self.token_stats.record_tokens(agent_role, model, input_tokens, output_tokens)
        
        # Создаем контекст для логирования
        kv = {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "prompt_id": prompt_id,
            "prompt_sha256": prompt_sha256,
            "run_id": run_id,
            "usage": usage,
            "finish_reason": finish_reason
        }
        
        if budget_remaining is not None:
            kv["budget_remaining"] = budget_remaining
            
        # Логируем вызов LLM
        logger.info(
            event="llm_call_end",
            component="llm",
            agent_role=agent_role,
            kv=kv
        )
        
        return kv

# Глобальный экземпляр счетчика токенов
token_accountant = TokenAccountant()

def get_token_accountant() -> TokenAccountant:
    """
    Получает глобальный экземпляр счетчика токенов.
    
    Returns:
        TokenAccountant: Глобальный экземпляр счетчика токенов
    """
    return token_accountant