#!/usr/bin/env python3
"""
artifact_manifest:
  files:
    - tests/test_health_integration.py
  package_contract:
    package_id: PKG-HEALTH-INTEGRATION-TEST-v1
    summary: Integration tests for health endpoints
    files_layout:
      - tests/test_health_integration.py
"""

import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
import subprocess
from fastapi.testclient import TestClient
from app.main import app

class TestHealthEndpointsIntegration(unittest.TestCase):
    """Интеграционные тесты для эндпоинтов проверки состояния здоровья приложения."""
    
    def setUp(self):
        """Подготовка к тестам."""
        self.client = TestClient(app)
        
        # Создаем временную базу данных для тестов
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.database_url = f"sqlite:///{self.temp_db_path}"
        
        # Устанавливаем переменную окружения для тестовой базы данных
        os.environ['DATABASE_URL'] = self.database_url
        os.environ['ENV'] = 'test'
        
        # Создаем таблицы в тестовой базе данных
        self._create_test_tables()
    
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
        
        # Создаем таблицу alembic_version
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL
            )
        """)
        
        # Добавляем тестовую версию миграции
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('abc123')")
        
        conn.commit()
        conn.close()
    
    def test_health_live_endpoint(self):
        """Тест эндпоинта /health/live."""
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["component"], "live")
    
    @patch('app.llm.cli_router.get_llm_providers')
    @patch('subprocess.run')
    def test_health_deps_endpoint_success(self, mock_subprocess_run, mock_get_llm_providers):
        """Тест успешного выполнения эндпоинта /health/deps."""
        # Настраиваем моки
        mock_get_llm_providers.return_value = {
            "qwen": {"cli_path": "/usr/local/bin/qwen-cli", "config": {"cmd": ["qwen-cli"]}},
            "gemini": {"cli_path": "/usr/local/bin/gemini-cli", "config": {"cmd": ["gemini-cli"]}}
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result
        
        # Выполняем запрос
        response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["component"], "deps")
        self.assertIn("checks", data)
    
    @patch('app.llm.cli_router.get_llm_providers')
    @patch('subprocess.run')
    def test_health_deps_endpoint_failure(self, mock_subprocess_run, mock_get_llm_providers):
        """Тест неуспешного выполнения эндпоинта /health/deps."""
        # Настраиваем моки
        mock_get_llm_providers.return_value = {
            "qwen": {"cli_path": "/usr/local/bin/qwen-cli", "config": {"cmd": ["qwen-cli"]}},
            "gemini": {"cli_path": "/usr/local/bin/gemini-cli", "config": {"cmd": ["gemini-cli"]}}
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        mock_subprocess_run.return_value = mock_result
        
        # Выполняем запрос
        response = self.client.get("/health/deps")
        # В текущей реализации это будет 503, так как все провайдеры в ошибке
        self.assertEqual(response.status_code, 503)
    
    def test_health_ready_endpoint_success(self):
        """Тест успешного выполнения эндпоинта /health/ready."""
        # Создаем необходимые файлы индекса
        data_dir = "/tmp/feature-factory-test-data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Сохраняем оригинальный путь
        original_data_path = "/opt/feature-factory/data"
        
        # Подменяем путь в функции check_index_files_health
        import app.api.health as health_module
        
        # Создаем тестовые файлы
        with open(os.path.join(data_dir, "code_registry.jsonl"), "w") as f:
            f.write("")
        with open(os.path.join(data_dir, "symbol_index.jsonl"), "w") as f:
            f.write("")
        with open(os.path.join(data_dir, "call_graph.dot"), "w") as f:
            f.write("")
        
        # Подменяем путь в функции проверки файлов
        original_check = health_module.check_index_files_health
        
        def mock_check_index_files_health():
            """Мок-функция для проверки файлов в тестовой директории."""
            try:
                # Проверяем наличие файлов индекса в тестовой директории
                required_files = ["code_registry.jsonl", "symbol_index.jsonl", "call_graph.dot"]
                
                missing_files = []
                for file in required_files:
                    if not os.path.exists(os.path.join(data_dir, file)):
                        missing_files.append(file)
                
                if missing_files:
                    return {"status": "error", "component": "index_files", "missing": missing_files}
                else:
                    return {"status": "ok", "component": "index_files"}
            except Exception as e:
                return {"status": "error", "component": "index_files", "error": str(e)}
        
        health_module.check_index_files_health = mock_check_index_files_health
        
        # Выполняем запрос
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["component"], "ready")
        
        # Восстанавливаем оригинальную функцию
        health_module.check_index_files_health = original_check
        
        # Убираем созданные файлы
        for filename in ["code_registry.jsonl", "symbol_index.jsonl", "call_graph.dot"]:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        os.rmdir(data_dir)

if __name__ == "__main__":
    unittest.main()