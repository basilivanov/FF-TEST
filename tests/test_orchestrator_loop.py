import unittest
import asyncio
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

# Импортируем планировщик
from app.orchestrator.loop import OrchestratorLoop


class TestOrchestratorLoop(unittest.TestCase):
    """Тесты для цикла оркестратора."""

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

    def test_smoke_loop_processing(self):
        """Smoke-тест лупа: создаёт задачу и доводит до DONE в TEST."""
        # Создаем фичу в БД
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url[10:]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Вставляем новую фичу
            cursor.execute("""
                INSERT INTO features (title, intent_json, status, priority, created_by, env)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Test Feature", '{"action": "test"}', 'NEW', 1, 'test', 'test'))
            
            feature_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Проверяем, что фича создана
            self.assertIsNotNone(feature_id)
            self.assertGreater(feature_id, 0)
            
            # Запускаем один цикл обработки
            # Так как функции асинхронные, оборачиваем в asyncio.run
            async def run_test():
                # Мокаем token_accountant, чтобы не было ошибок с бюджетом
                with patch('app.orchestrator.loop.get_token_accountant') as mock_token_accountant:
                    mock_accountant = MagicMock()
                    mock_accountant.can_spend.return_value = (True, 1000)
                    mock_token_accountant.return_value = mock_accountant
                    
                    # Обрабатываем бэклог
                    await self.loop._process_backlog()
                    
                    # Проверяем, что фича перешла в статус PLANNED
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,))
                    feature_row = cursor.fetchone()
                    conn.close()
                    
                    self.assertIsNotNone(feature_row)
                    self.assertEqual(feature_row[0], 'PLANNED')
                    
                    # Проверяем, что задачи были созданы
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM tasks WHERE feature_id = ?", (feature_id,))
                    task_count = cursor.fetchone()[0]
                    conn.close()
                    
                    self.assertGreater(task_count, 0)
                    self.assertEqual(task_count, 3)  # Dev, QA, Scribe задачи
            
            # Запускаем асинхронный тест
            asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()