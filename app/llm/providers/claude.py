#!/usr/bin/env python3
"""
Адаптер для провайдера Claude.
"""

import json
import os
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
from app.llm.providers.base import LLMProviderAdapter
import httpx

class ClaudeAdapter(LLMProviderAdapter):
    """Адаптер для провайдера Claude."""
    
    def __init__(self, provider_name="claude"):
        super().__init__(provider_name)
        self.provider_config = self.config.get(self.provider_name, {})
    
    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        """
        Формирует команду CLI и переменные окружения для вызова Claude.
        """
        # Базовая команда из конфигурации
        cmd = self.provider_config.get("cmd", ["claude", "messages", "create"])
        # Принудительно используем обёртку для стабильного окружения
        try:
            if cmd and isinstance(cmd, list):
                binary = cmd[0]
                if binary.endswith("/claude") or binary == "claude":
                    cmd[0] = "/opt/feature-factory/bin/claude"
        except Exception:
            # В случае аномальной конфигурации не мешаем дальнейшему выполнению
            pass
        
        # Переменные окружения
        env_vars = self.provider_config.get("env_required", [])
        # В окружение добавляем ТОЛЬКО непустые переменные, чтобы не затирать конфиги CLI пустыми значениями
        env = {}
        for var in env_vars:
            val = os.environ.get(var)
            if val:
                env[var] = val
        
        # Устанавливаем HOME для доступа к .claude.json
        env["HOME"] = "/home/feature"
        
        # Добавляем параметры/флаги из конфигурации
        flags = self.provider_config.get("flags", [])
        cmd.extend(flags)
        
        # Добавляем параметры модели, если они не включены в флаги
        model = self.provider_config.get("model")
        if model and "--model" not in cmd and "-m" not in cmd:
            cmd.extend(["--model", model])

        # Добавляем основные параметры
        # Claude CLI не поддерживает --max-tokens, --temperature, --stop-sequences
        # Используем только базовые опции

        # stdin: JSON messages
        import json as _json
        input_data = _json.dumps({"messages": messages}, ensure_ascii=False)

        return (cmd, env, input_data)
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Attempts to extract and parse a JSON object from a given text.
        Looks for the first occurrence of a JSON object enclosed in curly braces.
        """
        # This regex looks for a string that starts with '{' and ends with '}'
        # and tries to capture the content in between. It's a simple approach
        # and might need refinement for more complex cases.
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass # Fall through to raise error if extraction fails
        raise ValueError("No valid JSON object found in text.")

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout от CLI команды Claude и возвращает унифицированный контракт.
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
                raise ValueError(f"Failed to parse or extract JSON from Claude CLI output: {e}") from e

        if response_data is None:
            raise ValueError("Failed to obtain valid JSON response data from Claude CLI output.")

        # Формируем унифицированный контракт
        unified_response = {
            "provider": self.provider_name,
            "model": response_data.get("model", "unknown"),
            "text": response_data.get("content", [{}])[0].get("text", ""),
            "usage": response_data.get("usage", {
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated": True
            }),
            "finish_reason": response_data.get("stop_reason", "stop")
        }

        # Если usage не содержит токены, помечаем как оценочные
        if "input_tokens" not in unified_response["usage"] or "output_tokens" not in unified_response["usage"]:
            unified_response["usage"]["estimated"] = True
            unified_response["usage"]["input_tokens"] = unified_response["usage"].get("input_tokens", 0)
            unified_response["usage"]["output_tokens"] = unified_response["usage"].get("output_tokens", 0)

        return unified_response

    # --- OAuth2 Refresh flow (если поддерживается) ---
    def get_fresh_access_token(self, auth_cfg: Dict[str, Any]) -> str | None:
        """
        Пытается обновить access_token по refresh_token согласно параметрам в конфиге.
        Если недоступно/не настроено — возвращает None.
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
            with httpx.Client(timeout=20) as client:
                resp = client.post(token_endpoint, data=data)
                resp.raise_for_status()
                js = resp.json()
                return js.get("access_token")
        except Exception:
            return None

    def update_local_config_file(self, access_token: str, auth_cfg: Dict[str, Any]) -> None:
        """Пытается обновить локальный конфиг Claude с новым токеном.
        Если структура неизвестна — записывает минимальный JSON с access_token.
        """
        path = auth_cfg.get("local_config_file")
        if not path:
            return
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if p.exists():
                try:
                    import json as _json
                    data = _json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            # Попробуем обновить известные ключи
            updated = False
            for key in ("access_token", "session_token", "api_key"):
                if key in data:
                    data[key] = access_token
                    updated = True
            if not updated:
                data["access_token"] = access_token
            tmp = p.with_suffix(p.suffix + ".tmp")
            import json as _json
            tmp.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(p)
        except Exception:
            return
