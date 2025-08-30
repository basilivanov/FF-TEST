import unittest
import asyncio
import os
import tempfile
import sqlite3
import json
from unittest.mock import patch, MagicMock

# Импортируем планировщик
from app.orchestrator.loop import OrchestratorLoop


class TestLoopStability(unittest.TestCase):
    """Тесты для проверки стабильности лупа и обработки падений."""

    def setUp(self):
        """Подготовка перед каждым тестом."""
        # Создаем временную базу данных для тестов
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.database_url = f"sqlite:///{self.temp_db_path}"
        
        # Устанавливаем переменные окружения для тестовой базы данных
        os.environ['DATABASE_URL'] = self.database_url
        os.environ['ENV'] = 'test'
        
        # Создаем таблицы в тестовой базе данных
        self._create_test_tables(self.temp_db_path)
        
        # Создаем экземпляр планировщика
        self.loop = OrchestratorLoop()

    def tearDown(self):
        """Очистка после каждого теста."""
        # Останавливаем планировщик
        if hasattr(self.loop, 'running') and self.loop.running:
            asyncio.run(self.loop.stop())
        
        # Закрываем файл базы данных и удаляем его
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
        
        # Убираем переменные окружения
        env_vars_to_remove = ['DATABASE_URL', 'ENV']
        for var in env_vars_to_remove:
            if var in os.environ:
                del os.environ[var]

    @staticmethod
    def _create_test_tables(db_path):
        """Создает тестовые таблицы в базе данных."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем таблицы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                intent_json TEXT,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                env TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                dsl_json TEXT,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                budget_tokens INTEGER,
                scheduled_at DATETIME,
                started_at DATETIME,
                finished_at DATETIME
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_runs (
                run_id TEXT PRIMARY KEY,
                feature_id INTEGER NOT NULL,
                graph_name TEXT NOT NULL,
                thread_id TEXT,
                state_json TEXT,
                status TEXT,
                last_checkpoint_at DATETIME
            )
        """)
        
        conn.commit()
        conn.close()

    @patch('app.orchestrator.loop.logger')
    def test_budget_exceeded_handling(self, mock_logger):
        """Инъекция BudgetExceeded ⇒ задача уходит в WAIT_BUDGET."""
        # Создаем фичу и задачу в БД
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Вставляем новую фичу
            cursor.execute("""
                INSERT INTO features (title, intent_json, status, priority, created_by, env)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Test Feature", '{"action": "test"}', 'PLANNED', 1, 'test', 'test'))
            
            feature_id = cursor.lastrowid
            
            # Вставляем задачу в состоянии WAIT_BUDGET
            cursor.execute("""
                INSERT INTO tasks (feature_id, role, dsl_json, status, attempts, budget_tokens, scheduled_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (feature_id, 'Dev', '{"id": "test-task", "name": "test_task"}', 'WAIT_BUDGET', 0, 1000, ''))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Мокаем token_accountant, чтобы он возвращал недостаточный бюджет
            with patch('app.orchestrator.loop.get_token_accountant') as mock_token_accountant:
                mock_accountant = MagicMock()
                mock_accountant.can_spend.return_value = (False, 0)  # Бюджет превышен
                mock_token_accountant.return_value = mock_accountant
                
                # Запускаем обработку задач в состоянии WAIT_BUDGET
                async def run_test():
                    await self.loop._process_wait_budget_tasks()
                
                asyncio.run(run_test())
                
                # Проверяем, что задача все еще в состоянии WAIT_BUDGET (так как retry не превышен)
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT status, attempts FROM tasks WHERE id = ?", (task_id,))
                task_row = cursor.fetchone()
                conn.close()
                
                self.assertIsNotNone(task_row)
                # Счетчик попыток должен увеличиться
                self.assertEqual(task_row[1], 1)
                # Задача должна остаться в состоянии WAIT_BUDGET
                # (в реальной реализации она бы перешла в FAILED после 3 попыток)
                
                # Проверяем, что логи retry_scheduled присутствуют
                # Ищем вызов logger.info с event="wait_budget_task_retried"
                retry_log_found = False
                for call in mock_logger.info.call_args_list:
                    if call.kwargs.get('event') == 'wait_budget_task_retried':
                        retry_log_found = True
                        break
                
                self.assertTrue(retry_log_found, "Log event 'wait_budget_task_retried' not found")

    @patch('app.orchestrator.loop.logger')
    def test_retry_and_rate_limited_logs(self, mock_logger):
        """Проверка, что логи retry_scheduled/rate_limited присутствуют."""
        # Создаем фичу и задачу в БД
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Вставляем новую фичу
            cursor.execute("""
                INSERT INTO features (title, intent_json, status, priority, created_by, env)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Test Feature", '{"action": "test"}', 'PLANNED', 1, 'test', 'test'))
            
            feature_id = cursor.lastrowid
            
            # Вставляем задачу в состоянии WAIT_BUDGET с максимальным количеством попыток
            cursor.execute("""
                INSERT INTO tasks (feature_id, role, dsl_json, status, attempts, budget_tokens, scheduled_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (feature_id, 'Dev', '{"id": "test-task", "name": "test_task"}', 'WAIT_BUDGET', 3, 1000, ''))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Мокаем token_accountant, чтобы он возвращал недостаточный бюджет
            with patch('app.orchestrator.loop.get_token_accountant') as mock_token_accountant:
                mock_accountant = MagicMock()
                mock_accountant.can_spend.return_value = (False, 0)  # Бюджет превышен
                mock_token_accountant.return_value = mock_accountant
                
                # Запускаем обработку задач в состоянии WAIT_BUDGET
                async def run_test():
                    await self.loop._process_wait_budget_tasks()
                
                asyncio.run(run_test())
                
                # Проверяем, что задача перешла в состояние FAILED (так как retry превышен)
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT status, attempts FROM tasks WHERE id = ?", (task_id,))
                task_row = cursor.fetchone()
                conn.close()
                
                self.assertIsNotNone(task_row)
                # Задача должна перейти в состояние FAILED
                self.assertEqual(task_row[0], 'FAILED')
                
                # Проверяем, что лог rate_limited присутствует
                # Ищем вызов logger.info с event="wait_budget_task_failed_max_retries"
                rate_limited_log_found = False
                for call in mock_logger.info.call_args_list:
                    if call.kwargs.get('event') == 'wait_budget_task_failed_max_retries':
                        rate_limited_log_found = True
                        break
                
                self.assertTrue(rate_limited_log_found, "Log event 'wait_budget_task_failed_max_retries' not found")

    @patch('app.orchestrator.loop.logger')
    def test_no_500_errors(self, mock_logger):
        """Проверка, что нет 500 ошибок."""
        # Создаем фичу и задачу в БД
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Вставляем новую фичу
            cursor.execute("""
                INSERT INTO features (title, intent_json, status, priority, created_by, env)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Test Feature", '{"action": "test"}', 'PLANNED', 1, 'test', 'test'))
            
            feature_id = cursor.lastrowid
            
            # Вставляем задачу в состоянии WAIT_BUDGET
            cursor.execute("""
                INSERT INTO tasks (feature_id, role, dsl_json, status, attempts, budget_tokens, scheduled_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (feature_id, 'Dev', '{"id": "test-task", "name": "test_task"}', 'WAIT_BUDGET', 0, 1000, ''))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Мокаем token_accountant, чтобы он возвращал недостаточный бюджет
            with patch('app.orchestrator.loop.get_token_accountant') as mock_token_accountant:
                mock_accountant = MagicMock()
                mock_accountant.can_spend.return_value = (False, 0)  # Бюджет превышен
                mock_token_accountant.return_value = mock_accountant
                
                # Мокаем logger.error, чтобы проверить, что ошибок 500 нет
                mock_logger.error = MagicMock()
                
                # Запускаем обработку задач в состоянии WAIT_BUDGET
                async def run_test():
                    await self.loop._process_wait_budget_tasks()
                
                asyncio.run(run_test())
                
                # Проверяем, что не было вызова logger.error
                # Это означает, что не было 500 ошибок
                mock_logger.error.assert_not_called()

    def test_resume_on_next_slot(self):
        """Повторный проход на следующий слот возобновляет выполнение."""
        # Создаем фичу и задачу в БД
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Вставляем новую фичу
            cursor.execute("""
                INSERT INTO features (title, intent_json, status, priority, created_by, env)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Test Feature", '{"action": "test"}', 'PLANNED', 1, 'test', 'test'))
            
            feature_id = cursor.lastrowid
            
            # Вставляем задачу в состоянии WAIT_BUDGET
            cursor.execute("""
                INSERT INTO tasks (feature_id, role, dsl_json, status, attempts, budget_tokens, scheduled_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (feature_id, 'Dev', '{"id": "test-task", "name": "test_task"}', 'WAIT_BUDGET', 0, 1000, ''))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Мокаем token_accountant, чтобы он возвращал достаточный бюджет
            with patch('app.orchestrator.loop.get_token_accountant') as mock_token_accountant:
                mock_accountant = MagicMock()
                mock_accountant.can_spend.return_value = (True, 1000)  # Бюджет доступен
                mock_token_accountant.return_value = mock_accountant
                
                # Запускаем обработку задач в состоянии WAIT_BUDGET
                async def run_test():
                    await self.loop._process_wait_budget_tasks()
                
                asyncio.run(run_test())
                
                # Проверяем, что задача перешла в состояние NEW
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
                task_row = cursor.fetchone()
                conn.close()
                
                self.assertIsNotNone(task_row)
                self.assertEqual(task_row[0], 'NEW')


if __name__ == '__main__':
    unittest.main()