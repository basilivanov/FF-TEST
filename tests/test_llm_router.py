import unittest
from unittest.mock import patch, MagicMock
import json
from app.llm.router import completion, RETRYABLE_ERROR
from app.llm.transports.cli import run_cli, CliExecError, CliTimeoutError
from app.llm.token_budget import WAIT_BUDGET

class TestCliTransport(unittest.TestCase):
    """Тесты для транспорта CLI."""

    @patch('app.llm.transports.cli.subprocess.run')
    def test_run_cli_success(self, mock_run):
        """Тест успешного выполнения CLI команды."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"response": "test"}'
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        
        rc, stdout, stderr = run_cli(['echo', 'test'], {}, 10)
        
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, '{"response": "test"}')
        self.assertEqual(stderr, '')

    @patch('app.llm.transports.cli.subprocess.run')
    def test_run_cli_exec_error(self, mock_run):
        """Тест ошибки выполнения CLI команды."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Command failed'
        mock_run.return_value = mock_result
        
        with self.assertRaises(CliExecError):
            run_cli(['false'], {}, 10)

    @patch('app.llm.transports.cli.subprocess.run')
    def test_run_cli_timeout(self, mock_run):
        """Тест таймаута выполнения CLI команды."""
        mock_run.side_effect = CliTimeoutError("CLI command timed out")
        
        with self.assertRaises(CliTimeoutError):
            run_cli(['sleep', '10'], {}, 1)

class TestRouter(unittest.TestCase):
    """Тесты для роутера LLM."""

    def setUp(self):
        """Подготовка к тестам."""
        # Пример сообщений
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]

    @patch('app.llm.router.check_role_budget')
    @patch('app.llm.router.run_cli')
    @patch('app.llm.providers.qwen.QwenAdapter.parse_stdout')
    @patch('app.llm.providers.qwen.QwenAdapter.build_cmd')
    def test_completion_success(self, mock_build_cmd, mock_parse_stdout, mock_run_cli, mock_check_budget):
        """Тест успешного завершения через Qwen."""
        # Настраиваем моки
        mock_check_budget.return_value = None  # Бюджет не превышен
        mock_build_cmd.return_value = (['qwen', 'prompt'], {'QWEN_API_KEY': 'test'})
        mock_run_cli.return_value = (0, '{"response": "test"}', '')
        mock_parse_stdout.return_value = {
            "provider": "qwen",
            "model": "qwen3-coder:14b",
            "text": "I'm fine, thank you!",
            "usage": {"input_tokens": 10, "output_tokens": 5, "estimated": False},
            "finish_reason": "stop"
        }
        
        # Выполняем вызов
        result = completion("Dev", self.messages, 100, 0.7)
        
        # Проверяем результат
        self.assertEqual(result["provider"], "qwen")
        self.assertEqual(result["text"], "I'm fine, thank you!")
        self.assertEqual(result["usage"]["input_tokens"], 10)
        self.assertEqual(result["usage"]["output_tokens"], 5)
        mock_check_budget.assert_called_once()
        mock_build_cmd.assert_called_once()
        mock_run_cli.assert_called_once()
        mock_parse_stdout.assert_called_once()

    @patch('app.llm.router.check_role_budget')
    @patch('app.llm.router.run_cli')
    @patch('app.llm.providers.qwen.QwenAdapter.parse_stdout')
    @patch('app.llm.providers.qwen.QwenAdapter.build_cmd')
    def test_completion_qwen_fails_fallback_to_gemini(self, mock_build_cmd, mock_parse_stdout, mock_run_cli, mock_check_budget):
        """Тест fallback'а с Qwen на Gemini при ошибке."""
        # Настраиваем моки для Qwen (первый провайдер)
        mock_check_budget.return_value = None  # Бюджет не превышен
        mock_build_cmd.side_effect = [
            (['qwen', 'prompt'], {'QWEN_API_KEY': 'test'}),  # Вызов для Qwen
            (['gemini', 'prompt'], {'GEMINI_API_KEY': 'test'})  # Вызов для Gemini
        ]
        mock_run_cli.side_effect = [
            CliExecError("Qwen failed"),  # Ошибка Qwen
            (0, '{"response": "test"}', '')  # Успех Gemini
        ]
        mock_parse_stdout.return_value = {
            "provider": "gemini",
            "model": "gemini-pro",
            "text": "I'm doing well, thanks!",
            "usage": {"input_tokens": 8, "output_tokens": 6, "estimated": False},
            "finish_reason": "stop"
        }
        
        # Выполняем вызов
        result = completion("Dev", self.messages, 100, 0.7)
        
        # Проверяем результат
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["text"], "I'm doing well, thanks!")
        # Проверяем, что функции вызывались дважды (Qwen и Gemini)
        self.assertEqual(mock_build_cmd.call_count, 2)
        self.assertEqual(mock_run_cli.call_count, 2)
        mock_parse_stdout.assert_called_once()

    @patch('app.llm.router.check_role_budget')
    def test_completion_budget_exceeded(self, mock_check_budget):
        """Тест превышения бюджета."""
        # Настраиваем мок, чтобы выбрасывал исключение WAIT_BUDGET
        mock_check_budget.side_effect = WAIT_BUDGET("Budget exceeded")
        
        # Выполняем вызов и ожидаем исключение
        with self.assertRaises(WAIT_BUDGET):
            completion("Dev", self.messages, 100, 0.7)

    @patch('app.llm.router.check_role_budget')
    @patch('app.llm.router.run_cli')
    @patch('app.llm.providers.qwen.QwenAdapter.parse_stdout')
    @patch('app.llm.providers.qwen.QwenAdapter.build_cmd')
    def test_completion_retryable_error(self, mock_build_cmd, mock_parse_stdout, mock_run_cli, mock_check_budget):
        """Тест классификации ошибки как RETRYABLE_ERROR."""
        # Настраиваем моки
        mock_check_budget.return_value = None  # Бюджет не превышен
        mock_build_cmd.return_value = (['qwen', 'prompt'], {'QWEN_API_KEY': 'test'})
        mock_run_cli.side_effect = CliExecError("Command failed")
        mock_parse_stdout.return_value = {}
        
        # Выполняем вызов и ожидаем RETRYABLE_ERROR
        with self.assertRaises(RETRYABLE_ERROR):
            completion("Dev", self.messages, 100, 0.7)

    @patch('app.llm.router.check_role_budget')
    @patch('app.llm.router.run_cli')
    @patch('app.llm.providers.qwen.QwenAdapter.parse_stdout')
    @patch('app.llm.providers.qwen.QwenAdapter.build_cmd')
    def test_completion_json_parse_error(self, mock_build_cmd, mock_parse_stdout, mock_run_cli, mock_check_budget):
        """Тест ошибки парсинга JSON с fallback'ом."""
        # Настраиваем моки для Qwen (первый провайдер)
        mock_check_budget.return_value = None  # Бюджет не превышен
        mock_build_cmd.side_effect = [
            (['qwen', 'prompt'], {'QWEN_API_KEY': 'test'}),  # Вызов для Qwen
            (['gemini', 'prompt'], {'GEMINI_API_KEY': 'test'})  # Вызов для Gemini
        ]
        mock_run_cli.return_value = (0, '{"invalid": json}', '')  # Невалидный JSON
        mock_parse_stdout.side_effect = [
            ValueError("Invalid JSON"),  # Ошибка парсинга для Qwen
            {
                "provider": "gemini",
                "model": "gemini-pro",
                "text": "Parsed successfully",
                "usage": {"input_tokens": 5, "output_tokens": 3, "estimated": False},
                "finish_reason": "stop"
            }  # Успех для Gemini
        ]
        
        # Выполняем вызов
        result = completion("Dev", self.messages, 100, 0.7)
        
        # Проверяем результат
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["text"], "Parsed successfully")
        # Проверяем, что parse_stdout вызывался дважды
        self.assertEqual(mock_parse_stdout.call_count, 2)

if __name__ == '__main__':
    unittest.main()