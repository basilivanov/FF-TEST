"""
ChatAdapter - специальный адаптер для текстового чата.
Наследует от ClaudeAdapter но парсит простой текст вместо JSON.
"""

import json
import os
from typing import Dict, Any, List, Tuple
from app.llm.providers.claude import ClaudeAdapter


class ChatAdapter(ClaudeAdapter):
    """
    Адаптер для простого текстового чата.
    Использует Claude CLI но парсит ответ как обычный текст.
    """
    
    def __init__(self, provider_name="claude_chat"):
        super().__init__(provider_name)
    
    def complete(self, messages, max_tokens, temperature, stop=None, timeout_s=None):
        """Переопределяем complete чтобы добавить debug для CLI ошибок."""
        from app.llm.transports.cli import run_cli
        
        # Строим команду
        cmd, env, input_data = self.build_cmd(messages, max_tokens, temperature, stop)
        
        # Выполняем с debug
        timeout_s = timeout_s or 30
        return_code, stdout, stderr = run_cli(cmd, env, timeout_s=timeout_s, input_data=input_data)
        
        import structlog
        logger = structlog.get_logger()
        logger.info(f"[CHAT DEBUG] return_code: {return_code}")
        logger.info(f"[CHAT DEBUG] stderr: {stderr}")
        logger.info(f"[CHAT DEBUG] stdout length: {len(stdout)}")
        
        if return_code != 0:
            raise Exception(f"CLI command failed with code {return_code}: {stderr}")
        
        return self.parse_stdout(stdout)
    
    def build_cmd(self, messages: List[Dict[str, str]], max_tokens: int,
                  temperature: float, stop: List[str] = None) -> Tuple[List[str], Dict[str, str], str | None]:
        """
        Переопределяем build_cmd для текстового чата без неподдерживаемых параметров.
        """
        # Вызываем родительский метод но БЕЗ параметров max_tokens и temperature
        cmd, env, input_data = super().build_cmd(messages, 0, 0.0, None)
        
        # DEBUG: выводим команду для отладки
        import sys
        print(f"[CHAT DEBUG] Command: {' '.join(cmd)}", file=sys.stderr)
        print(f"[CHAT DEBUG] Input data length: {len(input_data)}", file=sys.stderr)
        
        return cmd, env, input_data

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout как простой текст, а не JSON.
        Возвращает унифицированный контракт с текстом в поле content.
        """
        # Очищаем текст от лишних пробелов и переносов
        clean_text = stdout.strip()
        
        # Формируем унифицированный контракт
        return {
            "provider": self.provider_name,
            "model": "claude-sonnet-4-20250514",  # из конфигурации
            "text": clean_text,
            "usage": {
                "input_tokens": 0,
                "output_tokens": max(10, len(clean_text) // 4),  # примерная оценка
                "estimated": True
            },
            "finish_reason": "stop",
            "choices": [{"message": {"content": clean_text}}]
        }