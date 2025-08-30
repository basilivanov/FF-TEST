import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from app.llm.token_accountant import TokenAccountant
from app.llm.token_budget import BudgetExceeded
from app.llm.token_stats import TokenStats

class TestTokenAccountant(unittest.TestCase):
    """Тесты для модуля учета токенов."""

    def setUp(self):
        """Подготовка к тестам."""
        self.token_accountant = TokenAccountant()
        
        # Мокаем token_stats
        self.token_accountant.token_stats = MagicMock()
        
        # Мокаем budgets
        self.token_accountant.budgets = {
            "Dev": 1400,
            "QA": 800,
            "Scribe": 800,
            "Architect": 1800,
            "Maintainer": 900
        }

    def test_estimate_tokens(self):
        """Тест оценки количества токенов."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Тестируем для разных провайдеров и моделей
        in_tokens, out_tokens = self.token_accountant.estimate_tokens("qwen", "qwen3-coder:14b", messages)
        self.assertGreater(in_tokens, 0)
        self.assertGreater(out_tokens, 0)
        
        in_tokens, out_tokens = self.token_accountant.estimate_tokens("gpt", "gpt-4o-mini", messages)
        self.assertGreater(in_tokens, 0)
        self.assertGreater(out_tokens, 0)

    def test_can_spend_success(self):
        """Тест успешной проверки возможности расхода токенов."""
        # Мокаем get_daily_stats чтобы вернуть пустую статистику
        self.token_accountant.token_stats.get_daily_stats.return_value = {}
        
        # Для роли Dev с лимитом 1400 токенов
        can_spend, remaining = self.token_accountant.can_spend("Dev", 100, 200)
        self.assertTrue(can_spend)
        self.assertEqual(remaining, 1400)

    def test_can_spend_exceeded(self):
        """Тест превышения бюджета токенов."""
        # Мокаем get_daily_stats чтобы вернуть статистику с использованными токенами
        self.token_accountant.token_stats.get_daily_stats.return_value = {
            "Dev": {
                "qwen3-coder:14b": {
                    "input_tokens": 1200,
                    "output_tokens": 100,
                    "total_calls": 10
                }
            }
        }
        
        # Для роли Dev с лимитом 1400 токенов уже использовано 1300
        # Попытка потратить еще 200 токенов должна привести к превышению
        can_spend, remaining = self.token_accountant.can_spend("Dev", 100, 150)
        self.assertFalse(can_spend)
        self.assertEqual(remaining, 1400 - 1300)  # 100 токенов осталось

    def test_record_usage(self):
        """Тест записи использования токенов."""
        # Проверяем, что record_tokens вызывается с правильными аргументами
        self.token_accountant.record_usage("Dev", "qwen", "qwen3-coder:14b", 100, 200, False)
        self.token_accountant.token_stats.record_tokens.assert_called_once_with("Dev", "qwen3-coder:14b", 100, 200)

class TestTokenBudget(unittest.TestCase):
    """Тесты для проверки бюджета токенов."""

    @patch('app.llm.token_budget.get_token_accountant')
    def test_check_role_budget_success(self, mock_get_token_accountant):
        """Тест успешной проверки бюджета."""
        # Мокаем token_accountant
        mock_token_accountant = MagicMock()
        mock_token_accountant.can_spend.return_value = (True, 1000)
        mock_get_token_accountant.return_value = mock_token_accountant
        
        # Импортируем функцию только после мокирования
        from app.llm.token_budget import check_role_budget
        
        # Вызов не должен выбрасывать исключение
        try:
            check_role_budget("Dev", 100)
        except BudgetExceeded:
            self.fail("check_role_budget() raised BudgetExceeded unexpectedly!")

    @patch('app.llm.token_budget.get_token_accountant')
    def test_check_role_budget_exceeded(self, mock_get_token_accountant):
        """Тест превышения бюджета."""
        # Мокаем token_accountant
        mock_token_accountant = MagicMock()
        mock_token_accountant.can_spend.return_value = (False, 50)
        mock_get_token_accountant.return_value = mock_token_accountant
        
        # Импортируем функцию только после мокирования
        from app.llm.token_budget import check_role_budget
        
        # Вызов должен выбрасывать исключение
        with self.assertRaises(BudgetExceeded):
            check_role_budget("Dev", 200)

if __name__ == '__main__':
    unittest.main()