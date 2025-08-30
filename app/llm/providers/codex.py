#!/usr/bin/env python3
"""
Адаптер для провайдера GPT-5 через Codex CLI (exec).
"""

from __future__ import annotations

import os
import json
import uuid
from typing import List, Dict, Any, Tuple

from app.llm.providers.base import LLMProviderAdapter
from app.llm.transports.cli import run_cli


class CodexAdapter(LLMProviderAdapter):
    """
    Адаптер, вызывающий Codex CLI в неинтерактивном режиме и извлекающий
    последний ответ агента через опцию --output-last-message.
    """

    def __init__(self, provider_name: str = "openai_gpt5_via_codex"):
        super().__init__(provider_name)
        self.provider_config = self.config.get(self.provider_name, {})

    def _format_messages_for_prompt(self, messages: List[Dict[str, str]]) -> str:
        # Переиспользуем формат из базового класса, но явно вызываем super()
        return super()._format_messages_for_prompt(messages)

    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        # Для Codex используем собственную сборку команды через exec
        cmd = self.provider_config.get("cmd", ["/opt/feature-factory/bin/codex"]) + [
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
            "-m", self.provider_config.get("model", "gpt-5"),
        ]

        # Вывод последнего сообщения агента в файл
        out_file = f"/tmp/ff_codex_last_{uuid.uuid4().hex}.txt"
        cmd.extend(["--output-last-message", out_file])

        # Переменные окружения (как правило не нужны для codex wrapper)
        env_vars = self.provider_config.get("env_required", [])
        env = {var: os.environ.get(var, "") for var in env_vars}

        # stdin: плоский prompt (склейка сообщений)
        prompt = self._format_messages_for_prompt(messages)

        # Сохраняем путь файла для последующего чтения в parse_stdout
        self._out_file = out_file

        return (cmd, env, prompt)

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        # Читаем последний ответ агента из файла, созданного Codex CLI
        text_content = ""
        try:
            if hasattr(self, "_out_file") and os.path.exists(self._out_file):
                with open(self._out_file, "r", encoding="utf-8") as f:
                    text_content = f.read().strip()
        finally:
            try:
                if hasattr(self, "_out_file") and os.path.exists(self._out_file):
                    os.remove(self._out_file)
            except Exception:
                pass

        # Возвращаем унифицированный контракт
        return {
            "provider": self.provider_name,
            "model": self.provider_config.get("model", "gpt-5"),
            "text": text_content,
            "usage": {"input_tokens": 0, "output_tokens": 0, "estimated": True},
            "finish_reason": "stop",
        }

    # OAuth refresh не требуется для Codex wrapper (управляет сам)
    def get_fresh_access_token(self, refresh_token: str, auth_cfg: Dict[str, Any]) -> str | None:
        return None
