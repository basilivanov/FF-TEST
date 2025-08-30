#!/usr/bin/env python3
"""
Простой тест для проверки работы can_spend без моков.
"""

import unittest
from app.llm.token_accountant import get_token_accountant

class TestTokenAccountantReal(unittest.TestCase):
    """Тест для проверки реального поведения TokenAccountant."""

    def test_can_spend_real(self):
        """Тест реального вызова can_spend."""
        # Получаем реальный экземпляр TokenAccountant
        token_accountant = get_token_accountant()
        
        # Проверяем, можно ли потратить токены
        can_spend, remaining = token_accountant.can_spend("Dev", 100, 50)
        
        print(f"can_spend: {can_spend}, remaining: {remaining}")
        
        # Просто проверяем, что метод не вызывает исключений
        self.assertIsInstance(can_spend, bool)
        if remaining is not None:
            self.assertIsInstance(remaining, int)

if __name__ == '__main__':
    unittest.main()