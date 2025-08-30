#!/usr/bin/env python3
"""
Адаптер для провайдера GPT.
"""

import json
import os
import re
from typing import List, Dict, Any, Tuple
from app.llm.providers.base import LLMProviderAdapter

class GPTAdapter(LLMProviderAdapter):
    """Адаптер для провайдера GPT."""
    
    def __init__(self, provider_name="gpt"):
        super().__init__(provider_name)
        self.provider_config = self.config.get(self.provider_name, {})
    
    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        """
        Формирует команду CLI и переменные окружения для вызова GPT.
        """
        # Базовая команда из конфигурации
        cmd = self.provider_config.get("cmd", ["openai", "chat.completions.create"])
        
        # Переменные окружения
        env_vars = self.provider_config.get("env_required", [])
        env = {var: os.environ.get(var, "") for var in env_vars}
        
        # Добавляем параметры
        flags = self.provider_config.get("flags", [])
        cmd.extend(flags)
        cmd.extend([
            "--max-tokens", str(max_tokens),
            "--temperature", str(temperature)
        ])

        if stop:
            # The codex CLI might expect stop sequences as a JSON array on stdin,
            # or as a comma-separated string. Assuming it's handled by the CLI
            # when messages are passed via stdin.
            # For now, we'll remove the explicit --stop argument.
            pass # Removed: cmd.extend(["--stop", json_module.dumps(stop)])

        # stdin: JSON messages
        import json as json_module
        input_data = json_module.dumps({"messages": messages}, ensure_ascii=False)

        return (cmd, env, input_data)
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Attempts to extract and parse a JSON object from a given text.
        Looks for the first occurrence of a JSON object enclosed in curly braces.
        """
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("No valid JSON object found in text.")

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout от CLI команды GPT и возвращает унифицированный контракт.
        """
        response_data = None
        try:
            # Пытаемся распарсить JSON напрямую
            response_data = json.loads(stdout)
        except json.JSONDecodeError:
            # Если не удалось, пытаемся извлечь JSON из текста
            try:
                response_data = self._extract_json_from_text(stdout)
            except ValueError as e:
                raise ValueError(f"Failed to parse or extract JSON from GPT CLI output: {e}") from e

        if response_data is None:
            raise ValueError("Failed to obtain valid JSON response data from GPT CLI output.")

        # Формируем унифицированный контракт
        unified_response = {
            "provider": self.provider_name,
            "model": response_data.get("model", "unknown"),
            "text": response_data.get("choices", [{}])[0].get("message", {}).get("content", ""),
            "usage": response_data.get("usage", {
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated": True
            }),
            "finish_reason": response_data.get("choices", [{}])[0].get("finish_reason", "stop")
        }

        # Если usage не содержит токены, помечаем как оценочные
        if "input_tokens" not in unified_response["usage"] or "output_tokens" not in unified_response["usage"]:
            unified_response["usage"]["estimated"] = True
            unified_response["usage"]["input_tokens"] = unified_response["usage"].get("input_tokens", 0)
            unified_response["usage"]["output_tokens"] = unified_response["usage"].get("output_tokens", 0)

        return unified_response
