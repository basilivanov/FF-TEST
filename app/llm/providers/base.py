#!/usr/bin/env python3
"""
Базовый класс для адаптеров провайдеров LLM.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import yaml

# Путь к конфигурационному файлу CLI
CLI_CONFIG_PATH = "/opt/feature-factory/configs/llm_cli.yaml"

class LLMProviderAdapter(ABC):
    """Абстрактный базовый класс для адаптеров провайдеров LLM."""
    
    def __init__(self, provider_name: str):
        """
        Инициализирует адаптер провайдера.
        
        Args:
            provider_name: Имя провайдера (например, 'qwen', 'gemini').
        """
        self.provider_name = provider_name
        self.config = self._load_cli_config()
    
    def _load_cli_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию CLI из файла."""
        if not os.path.exists(CLI_CONFIG_PATH):
            raise FileNotFoundError(f"CLI config file not found: {CLI_CONFIG_PATH}")
        
        with open(CLI_CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    
    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        """
        Формирует команду CLI, переменные окружения и stdin-дpayload для вызова провайдера.
        
        Args:
            messages: Список сообщений в формате OpenAI.
            max_tokens: Максимальное количество токенов в ответе.
            temperature: Температура генерации.
            stop: Список стоп-слов.
            
        Returns:
            Tuple[List[str], Dict[str, str], Optional[str]]: (команда, переменные окружения, stdin)
        """
        raise NotImplementedError("This provider does not implement build_cmd. Use complete() instead.")
    
    @abstractmethod
    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout от CLI команды и возвращает унифицированный контракт.
        
        Args:
            stdout: Вывод stdout от CLI команды.
            
        Returns:
            Dict[str, Any]: Унифицированный контракт ответа.
        """
        pass

    def _format_messages_for_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Форматирует сообщения в строку для передачи в CLI.
        
        Args:
            messages: Список сообщений.
            
        Returns:
            str: Отформатированная строка сообщений.
        """
        # Простое форматирование: роль: содержание\n
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        
        return "\n".join(prompt_parts)

    def complete(self, messages: List[Dict[str, str]], max_tokens: int,
                 temperature: float, stop: List[str] = None, timeout_s: int | None = None) -> Dict[str, Any]:
        """
        Выполняет completion через CLI команду.
        
        Args:
            messages: Список сообщений в формате OpenAI.
            max_tokens: Максимальное количество токенов в ответе.
            temperature: Температура генерации.
            stop: Список стоп-слов.
            
        Returns:
            Dict[str, Any]: Унифицированный контракт ответа.
        """
        from app.llm.transports.cli import run_cli
        import structlog
        logger = structlog.get_logger()

        try:
            # Строим команду через абстрактный метод
            cmd, env, input_data = self.build_cmd(messages, max_tokens, temperature, stop)
            logger.info(f"[BASE DEBUG] Provider: {self.provider_name}, cmd: {' '.join(cmd)}")
        except Exception as e:
            logger.error(f"[BASE DEBUG] build_cmd failed for {self.provider_name}: {e}")
            raise

        # Выполняем CLI команду с таймаутом (по умолчанию 30 секунд), передавая stdin при необходимости
        if timeout_s is None:
            timeout_s = 30
        return_code, stdout, stderr = run_cli(cmd, env, timeout_s=timeout_s, input_data=input_data)
        
        logger.info(f"[BASE DEBUG] return_code: {return_code}, stderr: {stderr}")
        
        if return_code != 0:
            raise Exception(f"CLI command failed with code {return_code}: {stderr}")
        
        # Универсальный парсинг на основе конфигурации output_parser
        provider_config = self.config.get(self.provider_name, {})
        output_parser = provider_config.get("output_parser", "json")
        
        logger.info(f"[BASE DEBUG] output_parser: {output_parser}")
        
        if output_parser == "text":
            # Для чата возвращаем простой текст в унифицированном формате
            return {
                "provider": self.provider_name,
                "model": provider_config.get("model", "unknown"),
                "text": stdout.strip(),
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": max(10, len(stdout) // 4),
                    "estimated": True
                },
                "finish_reason": "stop",
                "choices": [{"message": {"content": stdout.strip()}}]
            }
        else:
            # Для остальных случаев используем специфический парсинг адаптера
            return self.parse_stdout(stdout)
