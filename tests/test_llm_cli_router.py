from __future__ import annotations
import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from app.llm.cli_router import get_llm_providers

class TestLLMCLIProvider(unittest.TestCase):
    """Тесты для модуля получения провайдеров LLM CLI."""
    
    @patch("os.path.exists")
    def test_get_llm_providers_file_not_exists(self, mock_exists):
        """Тест получения провайдеров когда файл конфигурации не существует."""
        mock_exists.return_value = False
        providers = get_llm_providers()
        self.assertIsInstance(providers, dict)
        self.assertEqual(len(providers), 0)
    
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="""
qwen:
  cmd: ["qwen-cli", "--model", "qwen3-coder:14b"]
  env: ["QWEN_API_KEY"]
  expects: "json"

gemini:
  cmd: ["gemini-cli", "-p"]
  env: ["GEMINI_API_KEY"]
  expects: "json"
""")
    def test_get_llm_providers_with_config(self, mock_file, mock_exists):
        """Тест получения провайдеров с конфигом."""
        mock_exists.return_value = True
        providers = get_llm_providers()
        
        self.assertIsInstance(providers, dict)
        self.assertEqual(len(providers), 2)
        self.assertIn("qwen", providers)
        self.assertIn("gemini", providers)
        self.assertEqual(providers["qwen"]["cli_path"], "qwen-cli")
        self.assertEqual(providers["gemini"]["cli_path"], "gemini-cli")

if __name__ == "__main__":
    unittest.main()