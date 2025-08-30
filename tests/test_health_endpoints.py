from __future__ import annotations
import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

class TestHealthEndpoints(unittest.TestCase):
    """Тесты для эндпоинтов проверки состояния здоровья приложения."""
    
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
    
    @patch('app.llm.cli_path_guard._load_cli_config')
    @patch('app.llm.cli_path_guard._get_binary_path')
    @patch('os.path.exists')
    @patch('os.access')
    def test_health_deps_endpoint_success(self, mock_access, mock_path_exists, mock_get_binary_path, mock_load_config):
        """Тест успешного выполнения эндпоинта /health/deps."""
        # Настраиваем моки
        mock_load_config.return_value = {
            "qwen": {
                "cmd": ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"],
                "env": ["QWEN_API_KEY"],
                "expects": "json"
            },
            "stub": {
                "cmd": ["python3", "-c", "print('test')"],
                "env": [],
                "expects": "json"
            }
        }
        
        mock_get_binary_path.return_value = "/usr/local/bin/qwen"
        mock_path_exists.return_value = True
        mock_access.return_value = True
        
        # Выполняем запрос
        response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["component"], "deps")
        self.assertIn("checks", data)
    
    @patch('app.llm.cli_path_guard._load_cli_config')
    @patch('app.llm.cli_path_guard._get_binary_path')
    @patch('os.path.exists')
    def test_health_deps_endpoint_failure(self, mock_path_exists, mock_get_binary_path, mock_load_config):
        """Тест неуспешного выполнения эндпоинта /health/deps."""
        # Настраиваем моки
        mock_load_config.return_value = {
            "qwen": {
                "cmd": ["qwen", "--model", "qwen3-coder:14b", "--no-interactive", "-p"],
                "env": ["QWEN_API_KEY"],
                "expects": "json"
            }
        }
        
        mock_get_binary_path.return_value = "/usr/local/bin/qwen"
        mock_path_exists.return_value = False  # Файл не существует
        
        # Выполняем запрос
        response = self.client.get("/health/deps")
        # В текущей реализации это будет 200, но со статусом ok (всегда 200)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["component"], "deps")
        # Проверяем, что в checks есть информация об ошибке
        self.assertIn("checks", data)
        self.assertGreater(len(data["checks"]), 0)
        # Проверяем, что в providers есть информация об ошибке
        llm_check = data["checks"][0]
        self.assertEqual(llm_check["component"], "llm_cli")
        self.assertGreater(len(llm_check["providers"]), 0)
        # Проверяем, что провайдер имеет статус error
        provider = llm_check["providers"][0]
        self.assertEqual(provider["provider"], "qwen")
        self.assertEqual(provider["status"], "error")
    
    @patch('app.llm.cli_path_guard._load_cli_config')
    def test_health_deps_endpoint_cli_not_found(self, mock_load_config):
        """Тест эндпоинта /health/deps когда CLI бинарь не найден."""
        # Настраиваем моки для ошибки загрузки конфигурации
        mock_load_config.side_effect = Exception("Config file not found")
        
        # Выполняем запрос
        response = self.client.get("/health/deps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["component"], "deps")
    
    def test_health_ready_endpoint_success(self):
        """Тест успешного выполнения эндпоинта /health/ready."""
        # Создаем временную директорию для файлов индекса
        data_dir = tempfile.mkdtemp()
        
        # Подменяем путь в функции проверки файлов
        import app.api.health as health_module
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
        
        # Создаем необходимые файлы индекса
        with open(os.path.join(data_dir, "code_registry.jsonl"), "w") as f:
            f.write("")
        with open(os.path.join(data_dir, "symbol_index.jsonl"), "w") as f:
            f.write("")
        with open(os.path.join(data_dir, "call_graph.dot"), "w") as f:
            f.write("")
        
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["component"], "ready")
        
        # Восстанавливаем оригинальную функцию
        health_module.check_index_files_health = original_check
        
        # Убираем созданные файлы
        os.remove(os.path.join(data_dir, "code_registry.jsonl"))
        os.remove(os.path.join(data_dir, "symbol_index.jsonl"))
        os.remove(os.path.join(data_dir, "call_graph.dot"))
        os.rmdir(data_dir)
    
    def test_health_ready_endpoint_missing_index_files(self):
        """Тест эндпоинта /health/ready когда отсутствуют файлы индекса."""
        # Создаем временную директорию для файлов индекса
        data_dir = tempfile.mkdtemp()
        
        # Подменяем путь в функции проверки файлов
        import app.api.health as health_module
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
        
        # Убеждаемся, что файлы индекса отсутствуют
        # Удаляем файлы, если они существуют
        for filename in ["code_registry.jsonl", "symbol_index.jsonl", "call_graph.dot"]:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["component"], "ready")
        
        # Восстанавливаем оригинальную функцию
        health_module.check_index_files_health = original_check
        
        # Удаляем директорию
        os.rmdir(data_dir)

if __name__ == "__main__":
    unittest.main()