"""
GeminiChatAdapter - адаптер для текстового чата через Gemini.
Наследует от GeminiAdapter но возвращает текст вместо JSON.
"""

from typing import Dict, Any
from app.llm.providers.gemini import GeminiAdapter


class GeminiChatAdapter(GeminiAdapter):
    """
    Адаптер для простого текстового чата через Gemini.
    """
    
    def __init__(self, provider_name="gemini_chat"):
        super().__init__(provider_name)

    def parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """
        Парсит stdout как простой текст для чата.
        """
        clean_text = stdout.strip()
        
        return {
            "provider": self.provider_name,
            "model": "gemini-2.5-pro",
            "text": clean_text,
            "usage": {
                "input_tokens": 0,
                "output_tokens": max(10, len(clean_text) // 4),
                "estimated": True
            },
            "finish_reason": "stop",
            "choices": [{"message": {"content": clean_text}}]
        }