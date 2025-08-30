#!/usr/bin/env python3
"""
artifact_manifest:
  files:
    - tests/test_health_e2e_smoke.py
  package_contract:
    package_id: PKG-HEALTH-E2E-SMOKE-TEST-v1
    summary: E2E smoke test for health endpoints
    files_layout:
      - tests/test_health_e2e_smoke.py
"""

import unittest
import os
import tempfile
import sqlite3
from fastapi.testclient import TestClient
from app.main import app

class TestHealthE2ESmoke(unittest.TestCase):
    """E2E smoke тест для проверки всех трех эндпоинтов health check."""
    
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
    
    def test_health_endpoints_e2e_smoke(self):
        """E2E smoke тест, который дергает все 3 эндпоинта и проверяет JSON поля."""
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
        
        try:
            # Проверяем /health/live
            response = self.client.get("/health/live")
            self.assertEqual(response.status_code, 200)
            live_data = response.json()
            self.assertIn("status", live_data)
            self.assertIn("component", live_data)
            self.assertEqual(live_data["status"], "ok")
            self.assertEqual(live_data["component"], "live")
            
            # Проверяем /health/ready
            response = self.client.get("/health/ready")
            self.assertEqual(response.status_code, 200)
            ready_data = response.json()
            self.assertIn("status", ready_data)
            self.assertIn("component", ready_data)
            self.assertIn("checks", ready_data)
            self.assertEqual(ready_data["status"], "ok")
            self.assertEqual(ready_data["component"], "ready")
            
            # Проверяем /health/deps
            response = self.client.get("/health/deps")
            self.assertEqual(response.status_code, 200)
            deps_data = response.json()
            self.assertIn("status", deps_data)
            self.assertIn("component", deps_data)
            self.assertIn("checks", deps_data)
            # Может быть как ok, так и error в зависимости от наличия CLI бинарников
            self.assertIn(deps_data["status"], ["ok", "error"])
            self.assertEqual(deps_data["component"], "deps")
            
            # Проверяем структуру JSON полей
            for data in [live_data, ready_data, deps_data]:
                self.assertIsInstance(data, dict)
                self.assertIn("status", data)
                self.assertIn("component", data)
                
                # Проверяем, что нет лишних полей, кроме ожидаемых
                expected_fields = {"status", "component", "checks"}
                actual_fields = set(data.keys())
                self.assertTrue(actual_fields.issubset(expected_fields), 
                               f"Unexpected fields in response: {actual_fields - expected_fields}")
                
                # Проверяем типы значений
                self.assertIsInstance(data["status"], str)
                self.assertIsInstance(data["component"], str)
                
                # Если есть checks, проверяем их структуру
                if "checks" in data:
                    self.assertIsInstance(data["checks"], list)
                    for check in data["checks"]:
                        self.assertIsInstance(check, dict)
                        self.assertIn("status", check)
                        self.assertIn("component", check)
                        self.assertIsInstance(check["status"], str)
                        self.assertIsInstance(check["component"], str)
        finally:
            # Восстанавливаем оригинальную функцию
            health_module.check_index_files_health = original_check
            
            # Убираем созданные файлы
            os.remove(os.path.join(data_dir, "code_registry.jsonl"))
            os.remove(os.path.join(data_dir, "symbol_index.jsonl"))
            os.remove(os.path.join(data_dir, "call_graph.dot"))
            os.rmdir(data_dir)

if __name__ == "__main__":
    unittest.main()