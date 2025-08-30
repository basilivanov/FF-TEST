#!/usr/bin/env python3
"""
Адаптер для провайдера Gemini.
"""

import json
import os
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from app.llm.providers.base import LLMProviderAdapter
import httpx

class GeminiAdapter(LLMProviderAdapter):
    """Адаптер для провайдера Gemini."""
    
    def __init__(self, provider_name="gemini"):
        super().__init__(provider_name)
        # Брать конфиг по фактическому имени провайдера из YAML (например, gemini_25_pro)
        self.provider_config = self.config.get(self.provider_name, {})
    
    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        """
        Формирует команду CLI и переменные окружения для вызова Gemini.
        """
        # Базовая команда из конфигурации (используем неинтерактивный режим через -p)
        cmd = self.provider_config.get("cmd", ["gemini"])        
        
        # Переменные окружения
        env_vars = self.provider_config.get("env_required", [])
        # Добавляем только непустые значения переменных окружения
        env = {}
        for var in env_vars:
            val = os.environ.get(var)
            if val:
                env[var] = val
        
        # Устанавливаем HOME на каталог, где уже есть папка .gemini
        # Это исключает повторную авторизацию CLI
        env["HOME"] = "/opt/feature-factory"
        
        # Флаги из конфигурации (включают -m <model>)
        flags = self.provider_config.get("flags", [])
        cmd.extend(flags)
        # Формируем плоский prompt и передаём через -p
        prompt = self._format_messages_for_prompt(messages)
        cmd.extend(["-p", prompt])
        # stdin не используется
        return (cmd, env, None)
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Извлекает JSON-объект из текста, включая markdown блоки.
        """
        # Сначала ищем JSON в markdown блоках ```json...```
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Затем ищем просто JSON объект
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("No valid JSON object found in text.")

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout от CLI команды Gemini и возвращает унифицированный контракт.
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
                raise ValueError(f"Failed to parse or extract JSON from Gemini CLI output: {e}") from e

        if response_data is None:
            raise ValueError("Failed to obtain valid JSON response data from Gemini CLI output.")

        # Формируем унифицированный контракт
        unified_response = {
            "provider": self.provider_name,
            "model": response_data.get("model", "unknown"),
            "text": response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", ""),
            "usage": response_data.get("usage", {
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated": True
            }),
            "finish_reason": response_data.get("candidates", [{}])[0].get("finishReason", "stop")
        }

        # Если usage не содержит токены, помечаем как оценочные
        if "input_tokens" not in unified_response["usage"] or "output_tokens" not in unified_response["usage"]:
            unified_response["usage"]["estimated"] = True
            unified_response["usage"]["input_tokens"] = unified_response["usage"].get("input_tokens", 0)
            unified_response["usage"]["output_tokens"] = unified_response["usage"].get("output_tokens", 0)

        return unified_response

    # --- OAuth2 Refresh flow ---
    def get_fresh_access_token(self, auth_cfg: Dict[str, Any]) -> str | None:
        """
        Обновляет access_token по refresh_token через OAuth2 endpoint.
        Требуются: token_endpoint, client_id, client_secret.
        """
        try:
            token_endpoint = auth_cfg.get("token_endpoint")
            client_id = auth_cfg.get("client_id")
            client_secret = auth_cfg.get("client_secret")
            refresh_token = auth_cfg.get("refresh_token")
            if not (token_endpoint and client_id and client_secret and refresh_token):
                return None
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }
            # Доп. scope при необходимости
            if auth_cfg.get("scope"):
                data["scope"] = auth_cfg.get("scope")
            with httpx.Client(timeout=20) as client:
                resp = client.post(token_endpoint, data=data)
                resp.raise_for_status()
                js = resp.json()
                return js.get("access_token")
        except Exception:
            return None

    def update_local_config_file(self, access_token: str, auth_cfg: Dict[str, Any]) -> None:
        """Атомарно обновляет локальный файл oauth_creds.json для Gemini.
        Сохраняем и refresh_token, если он известен.
        """
        path = auth_cfg.get("local_config_file")
        if not path:
            return
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            # Сохраним refresh_token из auth_cfg если есть
            rt = auth_cfg.get("refresh_token")
            data = {}
            if p.exists():
                try:
                    import json as _json
                    data = _json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            data["access_token"] = access_token
            if rt:
                data["refresh_token"] = rt
            # Атомарная запись
            tmp = p.with_suffix(p.suffix + ".tmp")
            import json as _json
            tmp.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(p)
        except Exception:
            return
