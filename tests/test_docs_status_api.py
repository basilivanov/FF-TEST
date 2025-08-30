import unittest
import json
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Импортируем наше приложение
from app.main import app

class TestDocsStatusAPI(unittest.TestCase):
    """Тесты для API статуса документов."""
    
    def setUp(self):
        """Подготовка к тестам."""
        # Создаем временную базу данных для тестов
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.database_url = f"sqlite:///{self.temp_db_path}"
        
        # Устанавливаем переменную окружения для тестовой базы данных
        os.environ['DATABASE_URL'] = self.database_url
        os.environ['ENV'] = 'test'
        
        # Создаем таблицы в тестовой базе данных
        self._create_test_tables()
        
        # Создаем клиента для тестирования
        self.client = TestClient(app)
    
    def tearDown(self):
        """Очистка после тестов."""
        # Закрываем файл базы данных и удаляем его
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
        
        # Убираем переменную окружения
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def _create_test_tables(self):
        """Создает тестовые таблицы в базе данных."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу doc_registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doc_registry (
                doc_name TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        
        # Добавляем тестовые данные
        cursor.execute("""
            INSERT OR REPLACE INTO doc_registry 
            (doc_name, version, content_hash, updated_at)
            VALUES 
            ('docs/Architecture.md', '1.0.0', 'abc123', datetime('now')),
            ('docs/API-Orchestrator-001.md', '1.0.0', 'def456', datetime('now')),
            ('docs/QA-Policy-001.md', '1.0.0', 'ghi789', datetime('now'))
        """)
        
        conn.commit()
        conn.close()
    
    def test_get_docs_status_success(self):
        """Тест успешного получения статуса документов."""
        # Отправляем GET запрос
        response = self.client.get("/api/v1/docs/status")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("docs", response_data)
        self.assertIsInstance(response_data["docs"], list)
        self.assertGreater(len(response_data["docs"]), 0)
        
        # Проверяем структуру каждого документа
        for doc in response_data["docs"]:
            self.assertIn("doc_name", doc)
            self.assertIn("version", doc)
            self.assertIn("content_hash", doc)
            self.assertIn("updated_at", doc)
    
    def test_get_docs_status_empty(self):
        """Тест получения статуса документов из пустой таблицы."""
        # Очищаем таблицу
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doc_registry")
        conn.commit()
        conn.close()
        
        # Отправляем GET запрос
        response = self.client.get("/api/v1/docs/status")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("docs", response_data)
        self.assertIsInstance(response_data["docs"], list)
        self.assertEqual(len(response_data["docs"]), 0)
    
    def test_rebuild_docs_success(self):
        """Тест успешной пересборки документов."""
        # Отправляем POST запрос
        response = self.client.post("/api/v1/docs/rebuild")
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        response_data = response.json()
        self.assertIn("status", response_data)
        self.assertIn("message", response_data)
        self.assertIn("docs_updated", response_data)
        self.assertEqual(response_data["status"], "success")
        self.assertIsInstance(response_data["docs_updated"], int)
    
    @patch('app.api.docs_status.log.error')
    def test_get_docs_status_internal_error(self, mock_log_error):
        """Тест ошибки при получении статуса документов."""
        # Мокируем engine.connect для выбрасывания исключения
        with patch('app.api.docs_status.engine.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")
            
            # Отправляем GET запрос
            response = self.client.get("/api/v1/docs/status")
            
            # Проверяем статус ответа
            self.assertEqual(response.status_code, 500)
            
            # Проверяем структуру ответа
            response_data = response.json()
            self.assertIn("detail", response_data)
            self.assertEqual(response_data["detail"], "Failed to get docs status")
            
            # Проверяем, что ошибка была залогирована
            mock_log_error.assert_called()
    
    @patch('app.api.docs_status.log.error')
    def test_rebuild_docs_internal_error(self, mock_log_error):
        """Тест ошибки при пересборке документов."""
        # Мокируем engine.connect для выбрасывания исключения
        with patch('app.api.docs_status.engine.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")
            
            # Отправляем POST запрос
            response = self.client.post("/api/v1/docs/rebuild")
            
            # Проверяем статус ответа
            self.assertEqual(response.status_code, 500)
            
            # Проверяем структуру ответа
            response_data = response.json()
            self.assertIn("detail", response_data)
            self.assertEqual(response_data["detail"], "Failed to rebuild documentation")
            
            # Проверяем, что ошибка была залогирована
            mock_log_error.assert_called()

if __name__ == "__main__":
    unittest.main()