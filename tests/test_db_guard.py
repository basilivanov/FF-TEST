import unittest
from unittest.mock import patch
import os
from app.db.guard import guard_db_path, FAILED_NEEDS_ATTENTION

class TestDbGuard(unittest.TestCase):
    """Тесты для модуля защиты БД."""

    def test_guard_db_path_test_success(self):
        """Тест успешной проверки пути к БД в TEST окружении."""
        with patch.dict(os.environ, {"ENV": "TEST"}):
            # Проверяем правильный путь для TEST
            guard_db_path("sqlite:////opt/feature-factory/data/test.db")
            # Тест должен пройти без исключений

    def test_guard_db_path_prod_success(self):
        """Тест успешной проверки пути к БД в PROD окружении."""
        with patch.dict(os.environ, {"ENV": "PROD"}):
            # Проверяем правильный путь для PROD
            guard_db_path("sqlite:////opt/feature-factory/data/prod.db")
            # Тест должен пройти без исключений

    def test_guard_db_path_test_mismatch(self):
        """Тест несовпадения пути к БД в TEST окружении."""
        with patch.dict(os.environ, {"ENV": "TEST"}):
            # Проверяем неправильный путь для TEST
            with self.assertRaises(FAILED_NEEDS_ATTENTION):
                guard_db_path("sqlite:////opt/feature-factory/data/prod.db")

    def test_guard_db_path_prod_mismatch(self):
        """Тест несовпадения пути к БД в PROD окружении."""
        with patch.dict(os.environ, {"ENV": "PROD"}):
            # Проверяем неправильный путь для PROD
            with self.assertRaises(FAILED_NEEDS_ATTENTION):
                guard_db_path("sqlite:////opt/feature-factory/data/test.db")

    def test_guard_db_path_unknown_env(self):
        """Тест неизвестного окружения."""
        with patch.dict(os.environ, {"ENV": "STAGING"}):
            # Проверяем путь для неизвестного окружения
            with self.assertRaises(FAILED_NEEDS_ATTENTION):
                guard_db_path("sqlite:////opt/feature-factory/data/test.db")

    def test_guard_db_path_new_path(self):
        """Тест нового пути к БД."""
        with patch.dict(os.environ, {"ENV": "TEST"}):
            # Проверяем новый путь, которого нет в ожидаемых
            with self.assertRaises(FAILED_NEEDS_ATTENTION):
                guard_db_path("sqlite:////opt/feature-factory/data/new.db")

if __name__ == '__main__':
    unittest.main()