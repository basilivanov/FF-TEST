#!/usr/bin/env python3
"""
Адаптер для провайдера Qwen.
"""

import json
import os
import re
from typing import List, Dict, Any, Tuple
from app.llm.providers.base import LLMProviderAdapter
import httpx

class QwenAdapter(LLMProviderAdapter):
    """Адаптер для провайдера Qwen."""
    
    def __init__(self, provider_name="qwen"):
        super().__init__(provider_name)
        self.provider_config = self.config.get(self.provider_name, {})
    
    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        """
        Формирует команду CLI и переменные окружения для вызова Qwen.
        """
        # Базовая команда из конфигурации
        cmd = self.provider_config.get("cmd", ["qwen", "run"])
        
        # Переменные окружения
        env_vars = self.provider_config.get("env_required", [])
        env = {var: os.environ.get(var, "") for var in env_vars}
        
        # Добавляем параметры/флаги
        flags = self.provider_config.get("flags", [])
        cmd.extend(flags)
        cmd.extend([
            "--max-tokens", str(max_tokens),
            "--temperature", str(temperature)
        ])

        if stop:
            cmd.extend(["--stop", ",".join(stop)])

        # stdin: строковый prompt (qwen_code.stdin_mode=prompt)
        prompt = self._format_messages_for_prompt(messages)
        input_data = prompt

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
        Парсит stdout от CLI команды Qwen и возвращает унифицированный контракт.
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
                raise ValueError(f"Failed to parse or extract JSON from Qwen CLI output: {e}") from e

        if response_data is None:
            raise ValueError("Failed to obtain valid JSON response data from Qwen CLI output.")

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

    # Опционально поддерживаем refresh, если доступно
    def get_fresh_access_token(self, refresh_token: str, auth_cfg: Dict[str, Any]) -> str | None:
        try:
            token_endpoint = auth_cfg.get("token_endpoint")
            client_id = auth_cfg.get("client_id")
            client_secret = auth_cfg.get("client_secret")
            if not (token_endpoint and client_id and client_secret and refresh_token):
                return None
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }
            with httpx.Client(timeout=20) as client:
                resp = client.post(token_endpoint, data=data)
                resp.raise_for_status()
                js = resp.json()
                return js.get("access_token")
        except Exception:
            return None
